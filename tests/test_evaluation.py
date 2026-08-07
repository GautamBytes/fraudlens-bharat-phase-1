import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

import pandas as pd
import pytest

from fraudlens import evaluation
from fraudlens.evaluation import _rule_probabilities, evaluate_all


DATASET = Path("data/samples/phase2_dataset.csv")


def test_evaluation_reports_the_four_comparable_classifiers(tmp_path):
    bundle = evaluate_all(DATASET, tmp_path)
    report = bundle.to_dict()

    assert report["dataset"]["sha256"] == hashlib.sha256(DATASET.read_bytes()).hexdigest()
    assert report["dataset"]["present_labels"] == sorted(report["dataset"]["present_labels"])
    assert report["dataset"]["missing_labels"] == ["legitimate"]
    assert report["dataset"]["phase2_target_met"] is False
    assert list(report["classifiers"]) == [
        "calibrated_tfidf",
        "marker_tfidf",
        "raw_tfidf",
        "rule_only",
    ]
    assert report["classifiers"]["marker_tfidf"]["selection_status"] == "ablation_not_selected"
    assert report["classifiers"]["calibrated_tfidf"]["selection_status"] == "selected"
    with pytest.raises(TypeError):
        bundle.document["schema_version"] = 2

    for classifier in report["classifiers"].values():
        assert classifier["threshold_selected_on"] == "validation"
        assert classifier["split_rows"] == {"train": 48, "validation": 8, "test": 8}
        assert classifier["test"]["rows"] == 8
        assert classifier["test"]["split"] == "test"
        assert 0.0 <= classifier["test"]["expected_calibration_error"] <= 1.0
        assert 0.0 <= classifier["test"]["coverage"] <= 1.0
        assert classifier["test"]["abstention_rate"] == 1.0 - classifier["test"]["coverage"]
        assert classifier["test"]["latency"]["method"]
        assert classifier["test"]["confusion_matrix_labels"] == sorted(
            classifier["test"]["per_class"]
        )


def test_evaluation_fits_tfidf_on_train_text_only_and_does_not_emit_holdout_text(tmp_path, monkeypatch):
    frame = pd.read_csv(DATASET)
    validation_secret = "unrepeatablevalidationtoken"
    test_secret = "unrepeatabletestonlytoken"
    frame.loc[frame["split"] == "validation", "text"] = frame.loc[
        frame["split"] == "validation", "text"
    ].map(lambda text: text + " " + validation_secret)
    frame.loc[frame["split"] == "test", "text"] = frame.loc[
        frame["split"] == "test", "text"
    ].map(lambda text: text + " " + test_secret)
    changed_dataset = tmp_path / "changed.csv"
    frame.to_csv(changed_dataset, index=False)

    observed_fit_text = []
    original_fit = evaluation._fit_deterministic_vectorizer

    def capture_fit(texts):
        observed_fit_text.extend(texts.tolist())
        return original_fit(texts)

    monkeypatch.setattr(evaluation, "_fit_deterministic_vectorizer", capture_fit)

    report = evaluate_all(changed_dataset, tmp_path / "result").to_dict()
    serialized = json.dumps(report, sort_keys=True)

    assert validation_secret not in observed_fit_text
    assert test_secret not in observed_fit_text
    assert validation_secret not in serialized
    assert test_secret not in serialized


def test_rule_baseline_abstains_for_a_future_label_without_markers():
    probabilities, evidence = _rule_probabilities(["An ordinary account notification."], ["legitimate"])

    assert probabilities.tolist() == [[1.0]]
    assert evidence.tolist() == [False]


def test_evaluation_json_and_summary_are_byte_identical_across_runs(tmp_path):
    first = tmp_path / "first"
    second = tmp_path / "second"

    evaluate_all(DATASET, first)
    evaluate_all(DATASET, second)

    assert (first / "evaluation.json").read_bytes() == (second / "evaluation.json").read_bytes()
    assert (first / "summary.txt").read_bytes() == (second / "summary.txt").read_bytes()


def test_evaluation_hash_changes_when_dataset_bytes_change(tmp_path):
    changed_dataset = tmp_path / "changed.csv"
    changed_dataset.write_bytes(DATASET.read_bytes() + b"\n")

    original = evaluate_all(DATASET, tmp_path / "original").to_dict()
    changed = evaluate_all(changed_dataset, tmp_path / "changed").to_dict()

    assert original["dataset"]["sha256"] != changed["dataset"]["sha256"]


def test_evaluation_cli_writes_the_document_and_readable_summary(tmp_path):
    environment = dict(os.environ, PYTHONPATH="src")
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "fraudlens.evaluation",
            "--dataset",
            str(DATASET),
            "--output",
            str(tmp_path / "phase2"),
        ],
        check=True,
        cwd=Path.cwd(),
        env=environment,
        capture_output=True,
        text=True,
    )

    assert "Test split results" in result.stdout
    assert (tmp_path / "phase2" / "evaluation.json").is_file()
    assert (tmp_path / "phase2" / "summary.txt").is_file()


def test_ci_workflow_runs_supported_versions_and_the_reproducibility_check():
    workflow = Path(".github/workflows/ci.yml").read_text(encoding="utf-8")

    assert "3.9" in workflow
    assert "3.11" in workflow
    assert "3.12" in workflow
    assert "contents: read" in workflow
    assert "actions/checkout@v4" in workflow
    assert "actions/setup-python@v5" in workflow
    assert "python -m compileall -q src tests" in workflow
    assert "python -m pytest" in workflow
    assert "fraudlens.evaluation" in workflow
    assert "cmp" in workflow
    assert "outputs/phase2/evaluation.json" in workflow
