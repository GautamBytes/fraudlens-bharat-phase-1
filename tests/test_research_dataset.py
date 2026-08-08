import json
from pathlib import Path

import pandas as pd

from fraudlens.data_contract import REQUIRED_COLUMNS
from fraudlens.research_dataset import (
    DatasetAudit,
    ResearchRow,
    audit_dataset,
    load_research_rows,
    write_dataset_audit,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATASET_PATH = PROJECT_ROOT / "data" / "samples" / "phase2_dataset.csv"


def _row(**overrides):
    values = {
        "id": "1",
        "text": "Verify your bank account now",
        "label": "kyc_scam",
        "source_type": "synthetic",
        "language_mix": "english",
        "template_group": "kyc-one",
        "split": "train",
        "provenance_id": "source-one",
        "license": "project-generated",
        "pii_reviewed": "True",
        "reviewer": "Research fixture",
        "notes": "Fixture row",
    }
    values.update(overrides)
    return ResearchRow(**values)


def test_load_research_rows_preserves_the_validated_experiment_fields():
    rows = load_research_rows(DATASET_PATH)

    assert len(rows) == 64
    assert rows[0].id == "1"
    assert rows[0].label == "kyc_scam"
    assert rows[0].split == "train"
    assert rows[0].provenance_id == "phase1-seed-synthetic"


def test_load_research_rows_rejects_missing_contract_columns(tmp_path):
    frame = pd.read_csv(DATASET_PATH).drop(columns=["provenance_id"])
    path = tmp_path / "invalid.csv"
    frame.to_csv(path, index=False)

    try:
        load_research_rows(path)
    except ValueError as error:
        assert str(error) == "research dataset missing required columns: provenance_id"
    else:
        raise AssertionError("missing provenance must be rejected")


def test_load_research_rows_enforces_the_full_training_data_contract(tmp_path):
    frame = pd.read_csv(DATASET_PATH)
    frame.loc[0, "label"] = "invented_fraud_label"
    path = tmp_path / "invalid-label.csv"
    frame.to_csv(path, index=False)

    try:
        load_research_rows(path)
    except ValueError as error:
        assert "invalid label values" in str(error)
    else:
        raise AssertionError("invalid research labels must be rejected")


def test_audit_records_balance_gaps_and_split_evidence():
    audit = audit_dataset(load_research_rows(DATASET_PATH))

    assert isinstance(audit, DatasetAudit)
    assert audit.row_count == 64
    assert audit.label_counts == {
        "courier_scam": 8,
        "digital_arrest": 8,
        "fake_job": 8,
        "investment_scam": 8,
        "kyc_scam": 8,
        "loan_scam": 8,
        "otp_phishing": 8,
        "upi_refund_scam": 8,
    }
    assert audit.split_counts == {"test": 8, "train": 48, "validation": 8}
    assert audit.language_counts == {"english": 36, "hinglish": 28}
    assert audit.missing_labels == ("legitimate",)
    assert audit.meets_phase2_target is False
    assert audit.template_groups_crossing_splits == ()
    assert audit.provenance_ids_crossing_splits == ("phase1-seed-synthetic",)


def test_audit_detects_normalized_duplicates_and_template_leakage():
    rows = (
        _row(),
        _row(
            id="2",
            text="  VERIFY your BANK account now! ",
            split="test",
            template_group="kyc-one",
        ),
    )

    audit = audit_dataset(rows)

    assert audit.normalized_duplicate_groups == (("1", "2"),)
    assert audit.template_groups_crossing_splits == ("kyc-one",)


def test_write_dataset_audit_is_deterministic_and_machine_readable(tmp_path):
    audit = audit_dataset(load_research_rows(DATASET_PATH))
    first = tmp_path / "first.json"
    second = tmp_path / "second.json"

    write_dataset_audit(audit, first)
    write_dataset_audit(audit, second)

    assert first.read_bytes() == second.read_bytes()
    payload = json.loads(first.read_text(encoding="utf-8"))
    assert payload["schema_version"] == 1
    assert payload["row_count"] == 64
    assert payload["required_columns"] == list(REQUIRED_COLUMNS)
    assert payload["limitations"] == [
        "synthetic_only",
        "missing_legitimate_label",
        "below_200_examples_per_label",
        "frozen_test_has_one_row_per_present_label",
    ]
