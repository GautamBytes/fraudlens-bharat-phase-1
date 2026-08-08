"""Deterministic robustness, ablation, and paired-bootstrap evaluation."""

from __future__ import annotations

import argparse
import csv
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Sequence

import numpy as np
from sklearn.metrics import f1_score

from fraudlens import model_inference
from fraudlens.research_benchmark import (
    _aligned_probabilities,
    _model_text,
    _probability_predictions,
    _selective_predictions,
    _threshold,
)
from fraudlens.research_dataset import ResearchRow, load_research_rows
from fraudlens.research_metrics import classification_metrics
from fraudlens.research_models import build_candidate_models, build_estimator


PERTURBATIONS = (
    "case_and_punctuation",
    "whitespace",
    "hinglish_spelling",
    "digit_masking",
    "ocr_confusion",
)
_SEED = 42
_CSV_FIELDS = (
    "model",
    "condition",
    "accuracy",
    "macro_f1",
    "coverage",
    "accepted_accuracy",
    "macro_f1_drop_from_clean",
)


@dataclass(frozen=True)
class BootstrapInterval:
    point_delta: float
    lower_95: float
    upper_95: float
    probability_a_superior: float
    samples: int
    seed: int


def perturb_text(text: str, perturbation: str, seed: int = _SEED) -> str:
    """Apply bounded noise intended to preserve the original fraud label."""
    if perturbation == "case_and_punctuation":
        return re.sub(r"\s+", " ", re.sub(r"[^\w\s]", "", text.lower())).strip()
    if perturbation == "whitespace":
        words = text.split()
        return "".join(
            word + ("  " if (index + seed) % 2 == 0 else "   ")
            for index, word in enumerate(words)
        ).rstrip()
    if perturbation == "hinglish_spelling":
        replacements = {
            "aapka": "apka",
            "aapki": "apki",
            "karo": "kro",
            "karna": "krna",
            "please": "plz",
            "rupees": "rs",
            "hai": "h",
            "hoga": "hga",
        }
        result = text
        for source, target in replacements.items():
            result = re.sub(rf"\b{source}\b", target, result, flags=re.IGNORECASE)
        return result
    if perturbation == "digit_masking":
        return re.sub(r"\d", "0", text)
    if perturbation == "ocr_confusion":
        mapping = {"o": "0", "l": "1", "i": "1", "s": "5", "b": "8"}
        characters = list(text)
        replaced = False
        for index, character in enumerate(characters):
            replacement = mapping.get(character.lower())
            if replacement is not None and (index + seed) % 5 == 0:
                characters[index] = replacement
                replaced = True
        if not replaced:
            for index, character in enumerate(characters):
                replacement = mapping.get(character.lower())
                if replacement is not None:
                    characters[index] = replacement
                    break
        return "".join(characters)
    raise ValueError("unknown perturbation: {}".format(perturbation))


def paired_bootstrap_delta(
    y_true: Sequence[str],
    predictions_a: Sequence[str],
    predictions_b: Sequence[str],
    seed: int = _SEED,
    samples: int = 2000,
) -> BootstrapInterval:
    """Estimate the paired macro-F1 difference without breaking row pairing."""
    if not y_true or len(y_true) != len(predictions_a) or len(y_true) != len(predictions_b):
        raise ValueError("paired bootstrap inputs must be non-empty and equally sized")
    if samples < 1:
        raise ValueError("samples must be positive")
    labels = sorted(set(y_true))
    truth = np.asarray(y_true, dtype=object)
    first = np.asarray(predictions_a, dtype=object)
    second = np.asarray(predictions_b, dtype=object)
    point = _macro_f1(truth, first, labels) - _macro_f1(truth, second, labels)
    generator = np.random.default_rng(seed)
    deltas = np.empty(samples, dtype=float)
    for index in range(samples):
        selected = generator.integers(0, len(truth), size=len(truth))
        deltas[index] = _macro_f1(truth[selected], first[selected], labels) - _macro_f1(
            truth[selected], second[selected], labels
        )
    return BootstrapInterval(
        point_delta=_number(point),
        lower_95=_number(np.quantile(deltas, 0.025)),
        upper_95=_number(np.quantile(deltas, 0.975)),
        probability_a_superior=_number(float((deltas > 0).mean())),
        samples=samples,
        seed=seed,
    )


def run_robustness_benchmark(
    dataset_path: Path | str,
    output_dir: Path | str,
    bootstrap_samples: int = 2000,
) -> dict[str, object]:
    """Evaluate clean and perturbed frozen test rows under one fixed protocol."""
    rows = load_research_rows(dataset_path)
    train = tuple(row for row in rows if row.split == "train")
    validation = tuple(row for row in rows if row.split == "validation")
    test = tuple(row for row in rows if row.split == "test")
    if not train or not validation or not test:
        raise ValueError("research robustness requires train, validation, and test rows")
    labels = sorted({row.label for row in train})
    y_validation = [row.label for row in validation]
    y_test = [row.label for row in test]

    model_results: dict[str, object] = {}
    clean_predictions: dict[str, list[str]] = {}
    for candidate in build_candidate_models(seed=_SEED):
        threshold = None
        estimator = None
        if candidate.fit_required:
            estimator = build_estimator(candidate, seed=_SEED)
            estimator.fit([_model_text(row.text) for row in train], [row.label for row in train])
            validation_probabilities = _aligned_probabilities(
                estimator, [_model_text(row.text) for row in validation], labels
            )
            threshold = _threshold(y_validation, validation_probabilities, labels)

        conditions: dict[str, object] = {}
        condition_predictions: dict[str, list[str]] = {}
        for condition in ("clean", *PERTURBATIONS):
            texts = [
                row.text if condition == "clean" else perturb_text(row.text, condition, _SEED)
                for row in test
            ]
            if estimator is None:
                predictions = [model_inference.rule_based_predict(text)[0] for text in texts]
                probabilities = None
            else:
                probabilities = _aligned_probabilities(
                    estimator, [_model_text(text) for text in texts], labels
                )
                raw_predictions = _probability_predictions(probabilities, labels)
                predictions = _selective_predictions(
                    raw_predictions, probabilities, float(threshold)
                )
            condition_predictions[condition] = predictions
            metrics = classification_metrics(y_test, predictions, labels, probabilities)
            conditions[condition] = metrics

        clean_macro_f1 = float(conditions["clean"]["macro_f1"])
        for metrics in conditions.values():
            metrics["macro_f1_drop_from_clean"] = _number(
                clean_macro_f1 - float(metrics["macro_f1"])
            )
        clean_predictions[candidate.name] = condition_predictions["clean"]
        model_results[candidate.name] = {
            "threshold": threshold,
            "conditions": conditions,
        }

    classical_names = [
        name for name in model_results if name not in {"rule_only", "word_tfidf_logistic_regression"}
    ]
    best_name = max(
        classical_names,
        key=lambda name: float(model_results[name]["conditions"]["clean"]["macro_f1"]),
    )
    baseline_name = "word_tfidf_logistic_regression"
    comparison = paired_bootstrap_delta(
        y_test,
        clean_predictions[best_name],
        clean_predictions[baseline_name],
        seed=_SEED,
        samples=bootstrap_samples,
    )
    document: dict[str, object] = {
        "schema_version": 1,
        "protocol": {
            "random_seed": _SEED,
            "perturbations": list(PERTURBATIONS),
            "bootstrap_samples": bootstrap_samples,
            "bootstrap_confidence": 0.95,
            "fit_split": "train",
            "threshold_selection_split": "validation",
            "evaluation_split": "frozen test",
        },
        "models": model_results,
        "paired_bootstrap": {
            "model_a": best_name,
            "model_b": baseline_name,
            **asdict(comparison),
            "interpretation": (
                "A positive interval supports model A only on this eight-row synthetic test; "
                "it is not external evidence."
            ),
        },
        "limitations": [
            "Perturbations are controlled simulations, not naturally collected noisy complaints.",
            "Eight test rows make confidence intervals wide and unstable.",
        ],
    }
    _write_outputs(document, Path(output_dir))
    return document


def _macro_f1(
    y_true: np.ndarray, predictions: np.ndarray, labels: Sequence[str]
) -> float:
    return float(
        f1_score(y_true, predictions, labels=list(labels), average="macro", zero_division=0)
    )


def _number(value: float) -> float:
    return round(float(value), 8)


def _write_outputs(document: dict[str, object], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "robustness_benchmark.json").write_text(
        json.dumps(document, indent=2, ensure_ascii=False, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    with (output_dir / "ablation_summary.csv").open(
        "w", newline="", encoding="utf-8"
    ) as stream:
        writer = csv.DictWriter(stream, fieldnames=_CSV_FIELDS)
        writer.writeheader()
        for model_name, result in document["models"].items():
            for condition, metrics in result["conditions"].items():
                writer.writerow(
                    {
                        "model": model_name,
                        "condition": condition,
                        "accuracy": metrics["accuracy"],
                        "macro_f1": metrics["macro_f1"],
                        "coverage": metrics["coverage"],
                        "accepted_accuracy": metrics["accepted_accuracy"],
                        "macro_f1_drop_from_clean": metrics["macro_f1_drop_from_clean"],
                    }
                )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--bootstrap-samples", type=int, default=2000)
    args = parser.parse_args()
    run_robustness_benchmark(args.dataset, args.output, args.bootstrap_samples)


if __name__ == "__main__":
    main()
