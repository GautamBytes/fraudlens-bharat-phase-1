from pathlib import Path

import pandas as pd
import pytest

from fraudlens.data_contract import (
    REQUIRED_COLUMNS,
    TRAINED_LABELS,
    DatasetSummary,
    load_phase2_dataset,
    validate_phase2_dataset,
)
from fraudlens.phase2_migration import migrate_phase1_seed_dataset


def _valid_rows():
    return [
        {
            "id": "row-1",
            "text": "A suspicious payment request.",
            "label": "upi_refund_scam",
            "source_type": "synthetic",
            "language_mix": "english",
            "template_group": "upi-refund-001",
            "split": "train",
            "provenance_id": "phase1-seed-synthetic",
            "license": "project-generated",
            "pii_reviewed": True,
            "reviewer": "Phase 1 manual review",
            "notes": "Test fixture.",
        },
        {
            "id": "row-2",
            "text": "A normal account balance notification.",
            "label": "legitimate",
            "source_type": "synthetic",
            "language_mix": "english",
            "template_group": "legitimate-001",
            "split": "validation",
            "provenance_id": "phase1-seed-synthetic",
            "license": "project-generated",
            "pii_reviewed": True,
            "reviewer": "Phase 1 manual review",
            "notes": "Test fixture.",
        },
    ]


def _frame():
    return pd.DataFrame(_valid_rows(), columns=REQUIRED_COLUMNS)


def test_load_phase2_dataset_reads_csv_and_validates_it(tmp_path):
    dataset_path = tmp_path / "phase2.csv"
    _frame().to_csv(dataset_path, index=False)

    loaded = load_phase2_dataset(dataset_path)

    assert list(loaded.columns) == list(REQUIRED_COLUMNS)
    assert len(loaded) == 2


def test_validate_phase2_dataset_returns_immutable_summary_with_counts():
    summary = validate_phase2_dataset(_frame(), minimum_per_label=0)

    assert isinstance(summary, DatasetSummary)
    assert summary.row_count == 2
    assert summary.label_counts == {"legitimate": 1, "upi_refund_scam": 1}
    assert summary.split_counts == {"train": 1, "validation": 1}
    assert summary.source_type_counts == {"synthetic": 2}
    assert summary.meets_phase2_target is False
    with pytest.raises((AttributeError, TypeError)):
        summary.label_counts["legitimate"] = 99


def test_rejects_missing_required_columns():
    with pytest.raises(ValueError, match="missing required columns"):
        validate_phase2_dataset(_frame().drop(columns=["notes"]))


def test_rejects_duplicate_ids():
    frame = _frame()
    frame.loc[1, "id"] = frame.loc[0, "id"]

    with pytest.raises(ValueError, match="duplicate id"):
        validate_phase2_dataset(frame)


def test_rejects_duplicate_normalized_texts():
    frame = _frame()
    frame.loc[1, "text"] = "  a SUSPICIOUS payment request.  "

    with pytest.raises(ValueError, match="duplicate normalized text"):
        validate_phase2_dataset(frame)


@pytest.mark.parametrize("text", ["", "   ", None])
def test_rejects_empty_text(text):
    frame = _frame()
    frame.loc[0, "text"] = text

    with pytest.raises(ValueError, match="empty text"):
        validate_phase2_dataset(frame)


def test_rejects_invalid_label():
    frame = _frame()
    frame.loc[0, "label"] = "unknown_scam"

    with pytest.raises(ValueError, match="invalid label"):
        validate_phase2_dataset(frame)


def test_rejects_invalid_split():
    frame = _frame()
    frame.loc[0, "split"] = "holdout"

    with pytest.raises(ValueError, match="invalid split"):
        validate_phase2_dataset(frame)


@pytest.mark.parametrize("value", [False, "false", "no", 0, None])
def test_rejects_rows_without_confirmed_pii_review(value):
    frame = _frame()
    frame["pii_reviewed"] = frame["pii_reviewed"].astype(object)
    frame.loc[0, "pii_reviewed"] = value

    with pytest.raises(ValueError, match="unreviewed PII"):
        validate_phase2_dataset(frame)


def test_rejects_template_group_crossing_splits():
    frame = _frame()
    frame.loc[1, "template_group"] = frame.loc[0, "template_group"]

    with pytest.raises(ValueError, match="template_group.*crosses splits"):
        validate_phase2_dataset(frame)


def test_rejects_missing_provenance_ids_when_provenance_is_supplied():
    provenance = pd.DataFrame({"provenance_id": ["another-source"]})

    with pytest.raises(ValueError, match="missing provenance IDs"):
        validate_phase2_dataset(_frame(), provenance)


def test_rejects_labels_below_requested_minimum():
    with pytest.raises(ValueError, match="minimum_per_label"):
        validate_phase2_dataset(_frame(), minimum_per_label=2)


def test_phase1_migration_is_deterministic_and_bootstrap_dataset_is_honest(tmp_path):
    project_root = Path(__file__).resolve().parents[1]
    source_path = project_root / "data" / "samples" / "phase1_seed_dataset.csv"
    destination_one = tmp_path / "phase2-one.csv"
    destination_two = tmp_path / "phase2-two.csv"

    migrate_phase1_seed_dataset(source_path, destination_one)
    migrate_phase1_seed_dataset(source_path, destination_two)

    first = load_phase2_dataset(destination_one)
    second = load_phase2_dataset(destination_two)
    pd.testing.assert_frame_equal(first, second)
    summary = validate_phase2_dataset(first, minimum_per_label=0)
    assert len(first) == 64
    assert "legitimate" not in set(first["label"])
    assert set(first["source_type"]) == {"synthetic"}
    assert set(first["reviewer"]) == {"Phase 1 manual review"}
    assert summary.meets_phase2_target is False
    assert set(first["split"]) <= {"train", "validation", "test"}
    assert set(first["label"]) == set(TRAINED_LABELS) - {"legitimate"}
