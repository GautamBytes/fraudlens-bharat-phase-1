"""Metrics for fair, uncertainty-aware research comparisons."""

from __future__ import annotations

from typing import Sequence

import numpy as np
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    matthews_corrcoef,
    precision_recall_fscore_support,
)


_DIGITS = 8


def multiclass_brier_score(
    y_true: Sequence[str], probabilities: np.ndarray, labels: Sequence[str]
) -> float:
    """Return mean squared probability error across every class."""
    matrix, true_indices = _validated_probabilities(y_true, probabilities, labels)
    targets = np.zeros_like(matrix, dtype=float)
    targets[np.arange(len(true_indices)), true_indices] = 1.0
    return _number(np.mean(np.sum(np.square(matrix - targets), axis=1)))


def expected_calibration_error(
    y_true: Sequence[str],
    probabilities: np.ndarray,
    labels: Sequence[str],
    bins: int = 10,
) -> float:
    """Measure confidence/accuracy disagreement using equal-width bins."""
    if bins < 1:
        raise ValueError("bins must be positive")
    matrix, true_indices = _validated_probabilities(y_true, probabilities, labels)
    predicted = matrix.argmax(axis=1)
    confidence = matrix.max(axis=1)
    total = len(true_indices)
    error = 0.0
    for index in range(bins):
        lower = index / bins
        upper = (index + 1) / bins
        selected = (confidence >= lower) & (
            confidence <= upper if index == bins - 1 else confidence < upper
        )
        if not selected.any():
            continue
        bin_accuracy = float((predicted[selected] == true_indices[selected]).mean())
        bin_confidence = float(confidence[selected].mean())
        error += abs(bin_accuracy - bin_confidence) * float(selected.sum() / total)
    return _number(error)


def classification_metrics(
    y_true: Sequence[str],
    y_pred: Sequence[str],
    labels: Sequence[str],
    probabilities: np.ndarray | None = None,
) -> dict[str, object]:
    """Calculate classification, selectivity, calibration, and error evidence."""
    if not y_true:
        raise ValueError("y_true must not be empty")
    if len(y_true) != len(y_pred):
        raise ValueError("y_true and y_pred must have equal length")
    label_list = list(labels)
    if not label_list:
        raise ValueError("labels must not be empty")

    precision, recall, f1, support = precision_recall_fscore_support(
        y_true, y_pred, labels=label_list, zero_division=0
    )
    _, _, micro_f1, _ = precision_recall_fscore_support(
        y_true, y_pred, labels=label_list, average="micro", zero_division=0
    )
    _, _, weighted_f1, _ = precision_recall_fscore_support(
        y_true, y_pred, labels=label_list, average="weighted", zero_division=0
    )
    accepted = np.asarray([prediction != "unknown" for prediction in y_pred], dtype=bool)
    true_array = np.asarray(y_true, dtype=object)
    predicted_array = np.asarray(y_pred, dtype=object)
    coverage = float(accepted.mean())
    accepted_accuracy = (
        float(accuracy_score(true_array[accepted], predicted_array[accepted]))
        if accepted.any()
        else None
    )
    confusion_labels = label_list + (["unknown"] if "unknown" not in label_list else [])

    result: dict[str, object] = {
        "rows": len(y_true),
        "accuracy": _number(accuracy_score(y_true, y_pred)),
        "balanced_accuracy": _number(float(np.mean(recall))),
        "macro_precision": _number(float(np.mean(precision))),
        "macro_recall": _number(float(np.mean(recall))),
        "macro_f1": _number(float(np.mean(f1))),
        "micro_f1": _number(micro_f1),
        "weighted_f1": _number(weighted_f1),
        "matthews_correlation_coefficient": _number(matthews_corrcoef(y_true, y_pred)),
        "coverage": _number(coverage),
        "abstention_rate": _number(1.0 - coverage),
        "accepted_accuracy": _optional_number(accepted_accuracy),
        "expected_calibration_error": None,
        "multiclass_brier_score": None,
        "per_class": {
            label: {
                "precision": _number(precision[index]),
                "recall": _number(recall[index]),
                "f1": _number(f1[index]),
                "support": int(support[index]),
            }
            for index, label in enumerate(label_list)
        },
        "confusion_matrix_labels": confusion_labels,
        "confusion_matrix": confusion_matrix(
            y_true, y_pred, labels=confusion_labels
        ).tolist(),
    }
    if probabilities is not None:
        result["expected_calibration_error"] = expected_calibration_error(
            y_true, probabilities, label_list
        )
        result["multiclass_brier_score"] = multiclass_brier_score(
            y_true, probabilities, label_list
        )
    return result


def _validated_probabilities(
    y_true: Sequence[str], probabilities: np.ndarray, labels: Sequence[str]
) -> tuple[np.ndarray, np.ndarray]:
    matrix = np.asarray(probabilities, dtype=float)
    if matrix.shape != (len(y_true), len(labels)):
        raise ValueError("probabilities shape must be rows by labels")
    if not len(y_true):
        raise ValueError("y_true must not be empty")
    label_ids = {label: index for index, label in enumerate(labels)}
    unknown = sorted(set(y_true) - set(label_ids))
    if unknown:
        raise ValueError("y_true contains values absent from labels: {}".format(", ".join(unknown)))
    if not np.isfinite(matrix).all() or (matrix < 0).any():
        raise ValueError("probabilities must be finite and non-negative")
    if not np.allclose(matrix.sum(axis=1), 1.0, atol=1e-8):
        raise ValueError("probability rows must sum to one")
    return matrix, np.asarray([label_ids[label] for label in y_true], dtype=int)


def _number(value: float) -> float:
    return round(float(value), _DIGITS)


def _optional_number(value: float | None) -> float | None:
    return None if value is None else _number(value)
