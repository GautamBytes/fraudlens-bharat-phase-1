import numpy as np
import pytest

from fraudlens.research_metrics import (
    classification_metrics,
    expected_calibration_error,
    multiclass_brier_score,
)


def test_classification_metrics_counts_abstentions_as_overall_errors():
    metrics = classification_metrics(
        y_true=["a", "a", "b", "b"],
        y_pred=["a", "unknown", "b", "a"],
        labels=["a", "b"],
    )

    assert metrics["accuracy"] == 0.5
    assert metrics["balanced_accuracy"] == 0.5
    assert metrics["macro_f1"] == pytest.approx(0.58333333)
    assert metrics["coverage"] == 0.75
    assert metrics["abstention_rate"] == 0.25
    assert metrics["accepted_accuracy"] == pytest.approx(2 / 3)
    assert metrics["confusion_matrix_labels"] == ["a", "b", "unknown"]
    assert metrics["confusion_matrix"] == [[1, 0, 1], [1, 1, 0], [0, 0, 0]]
    assert metrics["expected_calibration_error"] is None
    assert metrics["multiclass_brier_score"] is None


def test_probability_metrics_use_label_aligned_multiclass_probabilities():
    probabilities = np.asarray(
        [[0.8, 0.2], [0.6, 0.4], [0.3, 0.7], [0.55, 0.45]], dtype=float
    )

    assert multiclass_brier_score(
        ["a", "a", "b", "b"], probabilities, ["a", "b"]
    ) == pytest.approx(0.29625)
    assert expected_calibration_error(
        ["a", "a", "b", "b"], probabilities, ["a", "b"], bins=10
    ) == pytest.approx(0.3625)

    metrics = classification_metrics(
        y_true=["a", "a", "b", "b"],
        y_pred=["a", "a", "b", "a"],
        labels=["a", "b"],
        probabilities=probabilities,
    )
    assert metrics["multiclass_brier_score"] == pytest.approx(0.29625)
    assert metrics["expected_calibration_error"] == pytest.approx(0.3625)


def test_probability_metrics_reject_invalid_shapes_and_unknown_labels():
    with pytest.raises(ValueError, match="shape"):
        multiclass_brier_score(["a"], np.asarray([[0.2, 0.3, 0.5]]), ["a", "b"])

    with pytest.raises(ValueError, match="absent from labels"):
        expected_calibration_error(["c"], np.asarray([[0.5, 0.5]]), ["a", "b"])


def test_empty_inputs_are_rejected():
    with pytest.raises(ValueError, match="must not be empty"):
        classification_metrics([], [], ["a", "b"])
