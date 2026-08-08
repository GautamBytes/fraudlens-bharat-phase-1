import csv
import json
from pathlib import Path

from fraudlens.research_benchmark import run_benchmark
from fraudlens.research_models import build_candidate_models


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATASET_PATH = PROJECT_ROOT / "data" / "samples" / "phase2_dataset.csv"


def test_candidate_models_cover_rules_classical_character_and_hybrid_families():
    candidates = build_candidate_models(seed=42)

    assert [candidate.name for candidate in candidates] == [
        "rule_only",
        "word_tfidf_logistic_regression",
        "character_tfidf_logistic_regression",
        "word_character_tfidf_logistic_regression",
        "calibrated_word_character_tfidf",
    ]
    assert candidates[0].fit_required is False
    assert all(candidate.fit_required for candidate in candidates[1:])


def test_benchmark_uses_train_validation_and_test_for_distinct_purposes(tmp_path):
    report = run_benchmark(DATASET_PATH, tmp_path)
    document = report.to_dict()

    assert document["dataset"]["rows"] == 64
    assert document["dataset"]["split_rows"] == {
        "test": 8,
        "train": 48,
        "validation": 8,
    }
    assert document["protocol"]["fit_ids"] == [
        str(value) for value in sorted(int(value) for value in document["protocol"]["fit_ids"])
    ]
    assert len(document["protocol"]["fit_ids"]) == 48
    assert len(document["protocol"]["threshold_selection_ids"]) == 8
    assert len(document["protocol"]["single_evaluation_ids"]) == 8
    assert not (
        set(document["protocol"]["fit_ids"])
        & set(document["protocol"]["single_evaluation_ids"])
    )
    assert document["protocol"]["test_evaluation_calls_per_model"] == 1

    model_names = list(document["models"])
    assert model_names == [candidate.name for candidate in build_candidate_models(seed=42)]
    for name, result in document["models"].items():
        assert result["test"]["raw"]["rows"] == 8
        assert result["test"]["selective"]["rows"] == 8
        assert result["test"]["raw"]["coverage"] == 1.0 or name == "rule_only"
        assert result["fit_split"] in {"none", "train"}


def test_benchmark_outputs_are_canonical_while_runtime_latency_is_separate(tmp_path):
    first_dir = tmp_path / "first"
    second_dir = tmp_path / "second"

    run_benchmark(DATASET_PATH, first_dir)
    run_benchmark(DATASET_PATH, second_dir)

    assert (first_dir / "classification_benchmark.json").read_bytes() == (
        second_dir / "classification_benchmark.json"
    ).read_bytes()
    assert (first_dir / "classification_summary.csv").read_bytes() == (
        second_dir / "classification_summary.csv"
    ).read_bytes()
    payload = json.loads(
        (first_dir / "classification_benchmark.json").read_text(encoding="utf-8")
    )
    assert all(
        "latency" not in result["test"]["selective"]
        for result in payload["models"].values()
    )
    assert "latency" in payload["protocol"]["timing_note"].lower()

    with (first_dir / "classification_summary.csv").open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    assert len(rows) == 5
    assert list(rows[0]) == [
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
    ]
