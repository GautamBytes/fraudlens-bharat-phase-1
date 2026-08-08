"""Run the deterministic, same-split FraudLens academic model benchmark."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence

import numpy as np
from sklearn.calibration import CalibratedClassifierCV
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import FeatureUnion, Pipeline

from fraudlens import model_inference
from fraudlens.model_training import _select_threshold
from fraudlens.preprocessing import normalize_text
from fraudlens.research_dataset import ResearchRow, load_research_rows
from fraudlens.research_metrics import classification_metrics
from fraudlens.research_models import ResearchModel, build_candidate_models, build_estimator


_SEED = 42
_SPLITS = ("train", "validation", "test")
_SUMMARY_FIELDS = (
    "model",
    "accuracy",
    "balanced_accuracy",
    "macro_f1",
    "weighted_f1",
    "mcc",
    "coverage",
    "abstention_rate",
    "accepted_accuracy",
    "ece",
    "brier",
    "estimated_model_bytes",
)


@dataclass(frozen=True)
class BenchmarkReport:
    document: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return json.loads(json.dumps(self.document, ensure_ascii=False))


def run_benchmark(dataset_path: Path | str, output_dir: Path | str) -> BenchmarkReport:
    """Fit on train, select abstention on validation, and touch test once."""
    dataset = Path(dataset_path)
    rows = load_research_rows(dataset)
    split_rows = {split: tuple(row for row in rows if row.split == split) for split in _SPLITS}
    for split, values in split_rows.items():
        if not values:
            raise ValueError("research dataset has no {} rows".format(split))
    labels = sorted({row.label for row in split_rows["train"]})
    for split in ("validation", "test"):
        unseen = sorted({row.label for row in split_rows[split]} - set(labels))
        if unseen:
            raise ValueError("{} contains labels absent from train: {}".format(split, ", ".join(unseen)))

    models: dict[str, Any] = {}
    for candidate in build_candidate_models(seed=_SEED):
        models[candidate.name] = _evaluate_candidate(candidate, split_rows, labels)

    document = {
        "schema_version": 1,
        "dataset": {
            "filename": dataset.name,
            "sha256": hashlib.sha256(dataset.read_bytes()).hexdigest(),
            "rows": len(rows),
            "split_rows": {split: len(split_rows[split]) for split in sorted(split_rows)},
            "labels": labels,
            "missing_legitimate_label": "legitimate" not in labels,
        },
        "protocol": {
            "random_seed": _SEED,
            "fit_ids": _sorted_ids(split_rows["train"]),
            "threshold_selection_ids": _sorted_ids(split_rows["validation"]),
            "single_evaluation_ids": _sorted_ids(split_rows["test"]),
            "test_evaluation_calls_per_model": 1,
            "selection_rule": "threshold maximises validation correct-minus-incorrect; ties favour coverage",
            "timing_note": "Wall-clock latency is excluded from canonical evidence and must be measured separately.",
        },
        "models": models,
        "limitations": [
            "64 synthetic fraud-only rows",
            "one frozen test row per present class",
            "no legitimate examples",
            "not a production accuracy or external generalisation claim",
        ],
    }
    report = BenchmarkReport(document=document)
    _write_outputs(report, Path(output_dir))
    return report


def _evaluate_candidate(
    candidate: ResearchModel,
    split_rows: dict[str, tuple[ResearchRow, ...]],
    labels: Sequence[str],
) -> dict[str, Any]:
    y_validation = [row.label for row in split_rows["validation"]]
    y_test = [row.label for row in split_rows["test"]]
    if not candidate.fit_required:
        validation_predictions = [
            model_inference.rule_based_predict(row.text)[0] for row in split_rows["validation"]
        ]
        test_predictions = [
            model_inference.rule_based_predict(row.text)[0] for row in split_rows["test"]
        ]
        return {
            "family": "transparent_rules",
            "representation": candidate.representation,
            "fit_split": "none",
            "threshold": None,
            "threshold_selected_on": "not_applicable",
            "estimated_model_bytes": 0,
            "validation": _paired_metrics(
                y_validation, validation_predictions, validation_predictions, labels, None
            ),
            "test": _paired_metrics(y_test, test_predictions, test_predictions, labels, None),
        }

    estimator = build_estimator(candidate, seed=_SEED)
    train_texts = [_model_text(row.text) for row in split_rows["train"]]
    train_labels = [row.label for row in split_rows["train"]]
    estimator.fit(train_texts, train_labels)

    validation_probabilities = _aligned_probabilities(
        estimator, [_model_text(row.text) for row in split_rows["validation"]], labels
    )
    validation_raw = _probability_predictions(validation_probabilities, labels)
    threshold = _threshold(y_validation, validation_probabilities, labels)
    validation_selective = _selective_predictions(
        validation_raw, validation_probabilities, threshold
    )

    test_probabilities = _aligned_probabilities(
        estimator, [_model_text(row.text) for row in split_rows["test"]], labels
    )
    test_raw = _probability_predictions(test_probabilities, labels)
    test_selective = _selective_predictions(test_raw, test_probabilities, threshold)
    return {
        "family": "classical_nlp",
        "representation": candidate.representation,
        "calibration": "sigmoid_cv_3_train_only" if candidate.calibrated else "none",
        "fit_split": "train",
        "threshold": round(float(threshold), 8),
        "threshold_selected_on": "validation",
        "estimated_model_bytes": _estimated_model_bytes(estimator),
        "validation": _paired_metrics(
            y_validation,
            validation_raw,
            validation_selective,
            labels,
            validation_probabilities,
        ),
        "test": _paired_metrics(
            y_test, test_raw, test_selective, labels, test_probabilities
        ),
    }


def _paired_metrics(
    y_true: Sequence[str],
    raw_predictions: Sequence[str],
    selective_predictions: Sequence[str],
    labels: Sequence[str],
    probabilities: np.ndarray | None,
) -> dict[str, Any]:
    return {
        "raw": classification_metrics(y_true, raw_predictions, labels, probabilities),
        "selective": classification_metrics(
            y_true, selective_predictions, labels, probabilities
        ),
    }


def _aligned_probabilities(estimator, texts: Sequence[str], labels: Sequence[str]) -> np.ndarray:
    probabilities = np.asarray(estimator.predict_proba(texts), dtype=float)
    class_positions = {str(label): index for index, label in enumerate(estimator.classes_)}
    missing = sorted(set(labels) - set(class_positions))
    if missing:
        raise ValueError("estimator probabilities omit labels: {}".format(", ".join(missing)))
    return probabilities[:, [class_positions[label] for label in labels]]


def _probability_predictions(probabilities: np.ndarray, labels: Sequence[str]) -> list[str]:
    return [labels[index] for index in probabilities.argmax(axis=1).tolist()]


def _selective_predictions(
    predictions: Sequence[str], probabilities: np.ndarray, threshold: float
) -> list[str]:
    accepted = probabilities.max(axis=1) >= threshold
    return [prediction if accepted[index] else "unknown" for index, prediction in enumerate(predictions)]


def _threshold(
    y_true: Sequence[str], probabilities: np.ndarray, labels: Sequence[str]
) -> float:
    label_ids = {label: index for index, label in enumerate(labels)}
    encoded = np.asarray([label_ids[label] for label in y_true], dtype=int)
    return _select_threshold(encoded, probabilities)


def _model_text(text: str) -> str:
    return normalize_text(text)


def _sorted_ids(rows: Sequence[ResearchRow]) -> list[str]:
    return [row.id for row in sorted(rows, key=lambda row: int(row.id))]


def _estimated_model_bytes(estimator: Any) -> int:
    """Estimate fitted numerical/vocabulary payload without serializing runtime metadata."""
    if isinstance(estimator, Pipeline):
        return sum(_estimated_model_bytes(step) for _, step in estimator.steps)
    if isinstance(estimator, FeatureUnion):
        return sum(_estimated_model_bytes(step) for _, step in estimator.transformer_list)
    if isinstance(estimator, TfidfVectorizer):
        vocabulary_bytes = sum(len(term.encode("utf-8")) + 8 for term in estimator.vocabulary_)
        return vocabulary_bytes + int(estimator.idf_.nbytes)
    if isinstance(estimator, LogisticRegression):
        return int(estimator.coef_.nbytes + estimator.intercept_.nbytes + estimator.classes_.nbytes)
    if isinstance(estimator, CalibratedClassifierCV):
        total = 0
        for calibrated in estimator.calibrated_classifiers_:
            total += _estimated_model_bytes(calibrated.estimator)
            total += 16 * len(calibrated.calibrators)
        return total
    return 0


def _write_outputs(report: BenchmarkReport, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    document = report.to_dict()
    (output_dir / "classification_benchmark.json").write_text(
        json.dumps(document, indent=2, ensure_ascii=False, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    with (output_dir / "classification_summary.csv").open(
        "w", newline="", encoding="utf-8"
    ) as stream:
        writer = csv.DictWriter(stream, fieldnames=_SUMMARY_FIELDS)
        writer.writeheader()
        for name, result in document["models"].items():
            metrics = result["test"]["selective"]
            writer.writerow(
                {
                    "model": name,
                    "accuracy": metrics["accuracy"],
                    "balanced_accuracy": metrics["balanced_accuracy"],
                    "macro_f1": metrics["macro_f1"],
                    "weighted_f1": metrics["weighted_f1"],
                    "mcc": metrics["matthews_correlation_coefficient"],
                    "coverage": metrics["coverage"],
                    "abstention_rate": metrics["abstention_rate"],
                    "accepted_accuracy": metrics["accepted_accuracy"],
                    "ece": metrics["expected_calibration_error"],
                    "brier": metrics["multiclass_brier_score"],
                    "estimated_model_bytes": result["estimated_model_bytes"],
                }
            )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    run_benchmark(args.dataset, args.output)


if __name__ == "__main__":
    main()
