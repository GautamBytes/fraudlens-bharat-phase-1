"""Privacy-safe external SMS validation for the academic evidence package."""

from __future__ import annotations

import hashlib
import io
import argparse
import csv
import json
import math
import random
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Sequence

import numpy as np
from sklearn.calibration import CalibratedClassifierCV
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    balanced_accuracy_score,
    brier_score_loss,
    confusion_matrix,
    f1_score,
    matthews_corrcoef,
    precision_recall_fscore_support,
)
from sklearn.pipeline import Pipeline

from fraudlens.entity_extraction import extract_entities
from fraudlens.model_inference import ModelPredictor
from fraudlens.preprocessing import normalize_text
from fraudlens.research_benchmark import _estimated_model_bytes
from fraudlens.research_metrics import expected_calibration_error
from fraudlens.risk_scoring import score_risk
from fraudlens.url_risk import analyze_urls


UCI_SMS_DATASET_ID = 228
UCI_SMS_DOI = "10.24432/C5CC84"
UCI_SMS_LICENSE = "CC BY 4.0"
UCI_SMS_ARCHIVE_SHA256 = "1587ea43e58e82b14ff1f5425c88e17f8496bfcdb67a583dbff9eefaf9963ce3"
UCI_SMS_EXPECTED_ROWS = 5_574
_LABELS = ("ham", "spam")
_SPLITS = ("train", "validation", "test")


@dataclass(frozen=True)
class ExternalSmsRow:
    label: str
    text: str


@dataclass(frozen=True)
class GroupedSplit:
    rows: Mapping[str, tuple[ExternalSmsRow, ...]]
    manifest_sha256: str
    counts: Mapping[str, int]
    normalized_groups: int
    duplicate_rows: int

    def public_metadata(self) -> dict[str, object]:
        return {
            "rows": sum(self.counts.values()),
            "labels": list(_LABELS),
            "normalized_groups": self.normalized_groups,
            "duplicate_rows": self.duplicate_rows,
            "split_rows": {name: self.counts[name] for name in _SPLITS},
            "split_labels": {
                name: {
                    label: sum(row.label == label for row in self.rows[name])
                    for label in _LABELS
                }
                for name in _SPLITS
            },
            "group_to_split_manifest_sha256": self.manifest_sha256,
        }


def load_uci_sms_archive(
    path: Path | str,
    *,
    expected_sha256: str = UCI_SMS_ARCHIVE_SHA256,
    expected_rows: int = UCI_SMS_EXPECTED_ROWS,
) -> tuple[ExternalSmsRow, ...]:
    """Read the official archive only after its bytes match pinned provenance."""
    archive_bytes = Path(path).read_bytes()
    actual_sha256 = hashlib.sha256(archive_bytes).hexdigest()
    if actual_sha256 != expected_sha256:
        raise ValueError("UCI SMS archive checksum mismatch")
    try:
        with zipfile.ZipFile(io.BytesIO(archive_bytes)) as archive:
            member_names = [name for name in archive.namelist() if name == "SMSSpamCollection"]
            if member_names != ["SMSSpamCollection"]:
                raise ValueError("UCI SMS archive member is missing or ambiguous")
            payload = archive.read(member_names[0]).decode("utf-8")
    except (zipfile.BadZipFile, UnicodeDecodeError) as error:
        raise ValueError("UCI SMS archive is invalid") from error

    rows: list[ExternalSmsRow] = []
    for line_number, line in enumerate(payload.splitlines(), start=1):
        label, separator, text = line.partition("\t")
        if not separator or label not in _LABELS or not text.strip():
            raise ValueError(f"invalid UCI SMS row {line_number}")
        rows.append(ExternalSmsRow(label=label, text=text))
    if len(rows) != expected_rows:
        raise ValueError(
            f"UCI SMS row count mismatch: expected {expected_rows}, found {len(rows)}"
        )
    if {row.label for row in rows} != set(_LABELS):
        raise ValueError("UCI SMS labels must contain ham and spam")
    return tuple(rows)


def grouped_stratified_split(
    rows: Sequence[ExternalSmsRow], seed: int = 42
) -> GroupedSplit:
    """Create a stable 70/15/15 split without normalized-text leakage."""
    if not rows:
        raise ValueError("external SMS rows must not be empty")
    grouped: dict[str, list[ExternalSmsRow]] = {}
    for row in rows:
        if row.label not in _LABELS:
            raise ValueError("external SMS label must be ham or spam")
        normalized = normalize_text(row.text)
        if not normalized:
            raise ValueError("external SMS text must not normalize to empty")
        grouped.setdefault(normalized, []).append(row)
    conflicts = [
        normalized
        for normalized, values in grouped.items()
        if len({row.label for row in values}) != 1
    ]
    if conflicts:
        raise ValueError("normalized duplicate text has conflicting labels")

    assignment: dict[str, str] = {}
    for label_index, label in enumerate(_LABELS):
        label_groups = sorted(
            normalized
            for normalized, values in grouped.items()
            if values[0].label == label
        )
        if len(label_groups) < 3:
            raise ValueError("each label needs at least three normalized groups")
        random.Random(seed + label_index).shuffle(label_groups)
        train_count = max(1, round(len(label_groups) * 0.70))
        validation_count = max(1, round(len(label_groups) * 0.15))
        if train_count + validation_count >= len(label_groups):
            train_count = len(label_groups) - 2
            validation_count = 1
        for index, normalized in enumerate(label_groups):
            split = (
                "train"
                if index < train_count
                else "validation"
                if index < train_count + validation_count
                else "test"
            )
            assignment[normalized] = split

    split_rows: dict[str, list[ExternalSmsRow]] = {name: [] for name in _SPLITS}
    for normalized in sorted(grouped):
        split_rows[assignment[normalized]].extend(
            sorted(grouped[normalized], key=lambda row: (row.label, row.text))
        )
    frozen_rows = {name: tuple(split_rows[name]) for name in _SPLITS}
    for name, values in frozen_rows.items():
        if {row.label for row in values} != set(_LABELS):
            raise ValueError(f"{name} split must contain both labels")
    manifest_payload = "\n".join(
        f"{hashlib.sha256(normalized.encode('utf-8')).hexdigest()}\t{assignment[normalized]}"
        for normalized in sorted(assignment)
    ).encode("ascii")
    counts = {name: len(frozen_rows[name]) for name in _SPLITS}
    return GroupedSplit(
        rows=frozen_rows,
        manifest_sha256=hashlib.sha256(manifest_payload).hexdigest(),
        counts=counts,
        normalized_groups=len(grouped),
        duplicate_rows=len(rows) - len(grouped),
    )


def wilson_interval(successes: int, total: int) -> tuple[float, float]:
    """Return the two-sided 95% Wilson score interval."""
    if isinstance(successes, bool) or isinstance(total, bool) or total <= 0:
        raise ValueError("Wilson interval requires a positive integer total")
    if not isinstance(successes, int) or not isinstance(total, int) or not 0 <= successes <= total:
        raise ValueError("Wilson successes must be an integer between zero and total")
    z = 1.959963984540054
    proportion = successes / total
    denominator = 1 + z * z / total
    centre = (proportion + z * z / (2 * total)) / denominator
    margin = z * math.sqrt(
        proportion * (1 - proportion) / total + z * z / (4 * total * total)
    ) / denominator
    return round(centre - margin, 8), round(centre + margin, 8)


def paired_stratified_bootstrap(
    y_true: Sequence[str],
    candidate_a: Sequence[str],
    candidate_b: Sequence[str],
    *,
    samples: int = 2_000,
    seed: int = 42,
) -> dict[str, object]:
    """Bootstrap paired Macro-F1 differences while retaining class support."""
    if not y_true or len(y_true) != len(candidate_a) or len(y_true) != len(candidate_b):
        raise ValueError("paired predictions must have equal non-zero lengths")
    if samples < 1:
        raise ValueError("bootstrap samples must be positive")
    true = np.asarray(y_true, dtype=object)
    first = np.asarray(candidate_a, dtype=object)
    second = np.asarray(candidate_b, dtype=object)
    class_indices = [np.flatnonzero(true == label) for label in _LABELS]
    if any(len(indices) == 0 for indices in class_indices):
        raise ValueError("bootstrap input must contain ham and spam")
    rng = np.random.default_rng(seed)
    differences = np.empty(samples, dtype=float)
    for sample_index in range(samples):
        selected = np.concatenate(
            [rng.choice(indices, size=len(indices), replace=True) for indices in class_indices]
        )
        first_score = f1_score(true[selected], first[selected], labels=list(_LABELS), average="macro")
        second_score = f1_score(true[selected], second[selected], labels=list(_LABELS), average="macro")
        differences[sample_index] = second_score - first_score
    observed = f1_score(true, second, labels=list(_LABELS), average="macro") - f1_score(
        true, first, labels=list(_LABELS), average="macro"
    )
    return {
        "samples": samples,
        "macro_f1_difference": round(float(observed), 8),
        "confidence_interval_95": [
            round(float(np.quantile(differences, 0.025)), 8),
            round(float(np.quantile(differences, 0.975)), 8),
        ],
        "probability_candidate_b_better": round(float(np.mean(differences > 0)), 8),
    }


def write_json(document: Mapping[str, object], path: Path | str) -> None:
    """Write a canonical aggregate document with no non-standard NaN values."""
    Path(path).write_text(
        json.dumps(document, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def run_external_evaluation(
    archive_path: Path | str,
    output_dir: Path | str,
    *,
    expected_sha256: str = UCI_SMS_ARCHIVE_SHA256,
    expected_rows: int = UCI_SMS_EXPECTED_ROWS,
    bootstrap_samples: int = 2_000,
    predictor: object | None = None,
) -> dict[str, object]:
    """Train fixed binary candidates and emit aggregate-only external evidence."""
    rows = load_uci_sms_archive(
        archive_path,
        expected_sha256=expected_sha256,
        expected_rows=expected_rows,
    )
    split = grouped_stratified_split(rows, seed=42)
    train = split.rows["train"]
    test = split.rows["test"]
    train_texts = [normalize_text(row.text) for row in train]
    train_labels = [row.label for row in train]
    test_texts = [normalize_text(row.text) for row in test]
    test_labels = [row.label for row in test]

    estimators = {
        "word_tfidf_logistic_regression": _binary_pipeline("word", calibrated=False),
        "character_tfidf_logistic_regression": _binary_pipeline("character", calibrated=False),
        "calibrated_character_tfidf": _binary_pipeline("character", calibrated=True),
    }
    model_results: dict[str, dict[str, object]] = {}
    predictions: dict[str, list[str]] = {}
    for name, estimator in estimators.items():
        estimator.fit(train_texts, train_labels)
        labels = [str(value) for value in estimator.classes_]
        probabilities = np.asarray(estimator.predict_proba(test_texts), dtype=float)
        spam_position = labels.index("spam")
        spam_probabilities = probabilities[:, spam_position]
        predicted = [labels[index] for index in probabilities.argmax(axis=1).tolist()]
        predictions[name] = predicted
        model_results[name] = {
            "representation": (
                "word_ngrams_1_2" if name.startswith("word_") else "character_ngrams_3_5"
            ),
            "calibration": "sigmoid_cv_3_train_only" if name.startswith("calibrated_") else "none",
            "fit_split": "train",
            "decision_threshold": 0.5,
            "estimated_model_bytes": _estimated_model_bytes(estimator),
            "test": _binary_metrics(test_labels, predicted, spam_probabilities, probabilities, labels),
        }

    comparison = paired_stratified_bootstrap(
        test_labels,
        predictions["word_tfidf_logistic_regression"],
        predictions["character_tfidf_logistic_regression"],
        samples=bootstrap_samples,
        seed=42,
    )
    document: dict[str, object] = {
        "schema_version": 1,
        "dataset": {
            "name": "SMS Spam Collection",
            "uci_dataset_id": UCI_SMS_DATASET_ID,
            "doi": UCI_SMS_DOI,
            "license": UCI_SMS_LICENSE,
            "source_url": "https://archive.ics.uci.edu/dataset/228/sms+spam+collection",
            "archive_sha256": expected_sha256,
            **split.public_metadata(),
            "raw_messages_committed": False,
            "row_predictions_committed": False,
        },
        "protocol": {
            "random_seed": 42,
            "split": "normalized-text-grouped stratified 70/15/15",
            "training_data": "train only",
            "test_use": "single final aggregate evaluation",
            "bootstrap_samples": bootstrap_samples,
            "primary_comparison": (
                "character TF-IDF minus word TF-IDF test Macro-F1, paired stratified bootstrap"
            ),
        },
        "models": model_results,
        "primary_comparison": comparison,
        "runtime_ham_stress": _runtime_ham_stress(test, predictor or ModelPredictor()),
        "claim_boundary": (
            "Binary public-corpus validation is separate from the internal eight-class synthetic "
            "evaluation and does not establish production effectiveness."
        ),
    }
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    write_json(document, output / "external_sms_summary.json")
    _write_model_csv(model_results, output / "external_sms_models.csv")
    return document


def _binary_pipeline(kind: str, *, calibrated: bool):
    vectorizer = TfidfVectorizer(
        analyzer="word" if kind == "word" else "char_wb",
        ngram_range=(1, 2) if kind == "word" else (3, 5),
        lowercase=False,
        sublinear_tf=True,
        token_pattern=r"(?u)\b\w\w+\b" if kind == "word" else None,
    )
    pipeline = Pipeline(
        (
            ("features", vectorizer),
            (
                "classifier",
                LogisticRegression(
                    max_iter=2_000,
                    class_weight="balanced",
                    random_state=42,
                ),
            ),
        )
    )
    if calibrated:
        return CalibratedClassifierCV(estimator=pipeline, method="sigmoid", cv=3)
    return pipeline


def _binary_metrics(
    y_true: Sequence[str],
    y_pred: Sequence[str],
    spam_probabilities: np.ndarray,
    probabilities: np.ndarray,
    probability_labels: Sequence[str],
) -> dict[str, object]:
    precision, recall, f1, support = precision_recall_fscore_support(
        y_true, y_pred, labels=list(_LABELS), zero_division=0
    )
    accuracy = float(accuracy_score(y_true, y_pred))
    accuracy_successes = sum(true == predicted for true, predicted in zip(y_true, y_pred))
    spam_support = sum(value == "spam" for value in y_true)
    ham_support = sum(value == "ham" for value in y_true)
    spam_true_positive = sum(
        true == "spam" and predicted == "spam" for true, predicted in zip(y_true, y_pred)
    )
    ham_true_negative = sum(
        true == "ham" and predicted == "ham" for true, predicted in zip(y_true, y_pred)
    )
    aligned_probabilities = probabilities[:, [probability_labels.index(label) for label in _LABELS]]
    return {
        "support": len(y_true),
        "label_support": {label: int(support[index]) for index, label in enumerate(_LABELS)},
        "accuracy": round(accuracy, 8),
        "balanced_accuracy": round(float(balanced_accuracy_score(y_true, y_pred)), 8),
        "spam_precision": round(float(precision[1]), 8),
        "spam_recall": round(float(recall[1]), 8),
        "spam_f1": round(float(f1[1]), 8),
        "macro_f1": round(float(f1_score(y_true, y_pred, average="macro")), 8),
        "matthews_correlation_coefficient": round(float(matthews_corrcoef(y_true, y_pred)), 8),
        "spam_average_precision": round(
            float(average_precision_score(np.asarray(y_true) == "spam", spam_probabilities)), 8
        ),
        "brier_score": round(
            float(brier_score_loss(np.asarray(y_true) == "spam", spam_probabilities)), 8
        ),
        "expected_calibration_error": expected_calibration_error(
            y_true, aligned_probabilities, _LABELS
        ),
        "confusion_matrix_labels": list(_LABELS),
        "confusion_matrix": confusion_matrix(y_true, y_pred, labels=list(_LABELS)).tolist(),
        "confidence_intervals_95": {
            "accuracy": list(wilson_interval(accuracy_successes, len(y_true))),
            "spam_recall": list(wilson_interval(spam_true_positive, spam_support)),
            "ham_specificity": list(wilson_interval(ham_true_negative, ham_support)),
        },
    }


def _runtime_ham_stress(
    test_rows: Sequence[ExternalSmsRow], predictor: object
) -> dict[str, object]:
    ham_rows = [row for row in test_rows if row.label == "ham"]
    predictions: list[object] = []
    risk_levels: list[str] = []
    categories: dict[str, int] = {}
    for row in ham_rows:
        cleaned = normalize_text(row.text)
        prediction = predictor.predict(cleaned)
        predictions.append(prediction)
        entities = extract_entities(cleaned)
        urls = [entity.value for entity in entities if entity.type == "url"]
        risk_level, _, _, _ = score_risk(
            prediction.label,
            prediction.confidence,
            entities,
            analyze_urls(urls),
        )
        risk_levels.append(risk_level)
        if not prediction.abstained:
            categories[prediction.label] = categories.get(prediction.label, 0) + 1
    support = len(ham_rows)
    abstentions = sum(prediction.abstained for prediction in predictions)
    return {
        "support": support,
        "abstention_rate": round(abstentions / support, 8),
        "coverage": round((support - abstentions) / support, 8),
        "medium_or_high_escalation_rate": round(
            sum(level in {"medium", "high"} for level in risk_levels) / support, 8
        ),
        "high_risk_rate": round(sum(level == "high" for level in risk_levels) / support, 8),
        "non_abstained_category_distribution": dict(sorted(categories.items())),
        "interpretation": (
            "Stress test on held-out ham only; this is not legitimate-class accuracy."
        ),
    }


def _write_model_csv(models: Mapping[str, Mapping[str, object]], path: Path) -> None:
    fields = (
        "model",
        "accuracy",
        "balanced_accuracy",
        "spam_precision",
        "spam_recall",
        "spam_f1",
        "macro_f1",
        "mcc",
        "average_precision",
        "brier",
        "ece",
        "estimated_model_bytes",
    )
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for name in sorted(models):
            result = models[name]
            metrics = result["test"]
            writer.writerow(
                {
                    "model": name,
                    "accuracy": metrics["accuracy"],
                    "balanced_accuracy": metrics["balanced_accuracy"],
                    "spam_precision": metrics["spam_precision"],
                    "spam_recall": metrics["spam_recall"],
                    "spam_f1": metrics["spam_f1"],
                    "macro_f1": metrics["macro_f1"],
                    "mcc": metrics["matthews_correlation_coefficient"],
                    "average_precision": metrics["spam_average_precision"],
                    "brier": metrics["brier_score"],
                    "ece": metrics["expected_calibration_error"],
                    "estimated_model_bytes": result["estimated_model_bytes"],
                }
            )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--bootstrap-samples", type=int, default=2_000)
    arguments = parser.parse_args()
    run_external_evaluation(
        arguments.archive,
        arguments.output,
        bootstrap_samples=arguments.bootstrap_samples,
    )


if __name__ == "__main__":
    main()
