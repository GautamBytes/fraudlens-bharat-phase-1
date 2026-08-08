import csv
import json
from pathlib import Path

import pytest

from fraudlens.research_robustness import (
    PERTURBATIONS,
    paired_bootstrap_delta,
    perturb_text,
    run_robustness_benchmark,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATASET_PATH = PROJECT_ROOT / "data" / "samples" / "phase2_dataset.csv"


@pytest.mark.parametrize("name", PERTURBATIONS)
def test_perturbations_are_deterministic_and_nonempty(name):
    text = "Aapka OTP 482901 verify karo at https://bank.example/reset now!"

    first = perturb_text(text, name, seed=42)
    second = perturb_text(text, name, seed=42)

    assert first == second
    assert first.strip()


def test_named_perturbations_apply_expected_label_preserving_noise():
    text = "Aapka account verify karo, please pay 4829 rupees!"

    assert perturb_text(text, "case_and_punctuation", 42) == (
        "aapka account verify karo please pay 4829 rupees"
    )
    assert "  " in perturb_text(text, "whitespace", 42)
    assert "apka" in perturb_text(text, "hinglish_spelling", 42).lower()
    assert "0000" in perturb_text(text, "digit_masking", 42)
    assert perturb_text(text, "ocr_confusion", 42) != text


def test_unknown_perturbation_is_rejected():
    with pytest.raises(ValueError, match="unknown perturbation"):
        perturb_text("example", "destroy_semantics", 42)


def test_paired_bootstrap_reports_zero_for_identical_predictions():
    interval = paired_bootstrap_delta(
        ["a", "a", "b", "b"],
        ["a", "a", "b", "b"],
        ["a", "a", "b", "b"],
        seed=42,
        samples=500,
    )

    assert interval.point_delta == 0.0
    assert interval.lower_95 == 0.0
    assert interval.upper_95 == 0.0
    assert interval.probability_a_superior == 0.0


def test_paired_bootstrap_detects_a_clear_macro_f1_improvement():
    interval = paired_bootstrap_delta(
        ["a", "a", "b", "b"],
        ["a", "a", "b", "b"],
        ["b", "b", "a", "a"],
        seed=42,
        samples=500,
    )

    assert interval.point_delta == 1.0
    assert interval.lower_95 >= 0.5
    assert interval.upper_95 == 1.0
    assert interval.probability_a_superior == 1.0


def test_robustness_evidence_is_deterministic_and_complete(tmp_path):
    first = tmp_path / "first"
    second = tmp_path / "second"

    run_robustness_benchmark(DATASET_PATH, first, bootstrap_samples=500)
    run_robustness_benchmark(DATASET_PATH, second, bootstrap_samples=500)

    assert (first / "robustness_benchmark.json").read_bytes() == (
        second / "robustness_benchmark.json"
    ).read_bytes()
    assert (first / "ablation_summary.csv").read_bytes() == (
        second / "ablation_summary.csv"
    ).read_bytes()
    payload = json.loads(
        (first / "robustness_benchmark.json").read_text(encoding="utf-8")
    )
    assert payload["protocol"]["perturbations"] == list(PERTURBATIONS)
    assert payload["protocol"]["bootstrap_samples"] == 500
    assert len(payload["models"]) == 5
    for result in payload["models"].values():
        assert set(result["conditions"]) == {"clean", *PERTURBATIONS}
        assert result["conditions"]["clean"]["rows"] == 8
        assert result["conditions"]["clean"]["macro_f1_drop_from_clean"] == 0.0

    with (first / "ablation_summary.csv").open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    assert len(rows) == 5 * (len(PERTURBATIONS) + 1)
    assert list(rows[0]) == [
        "model",
        "condition",
        "accuracy",
        "macro_f1",
        "coverage",
        "accepted_accuracy",
        "macro_f1_drop_from_clean",
    ]
