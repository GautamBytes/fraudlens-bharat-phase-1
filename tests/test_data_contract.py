from pathlib import Path

import pandas as pd
import pytest

from fraudlens.data_contract import (
    PROVENANCE_REQUIRED_COLUMNS,
    REQUIRED_COLUMNS,
    TRAINED_LABELS,
    DatasetSummary,
    load_phase2_dataset,
    validate_phase2_dataset,
)
from fraudlens.phase2_migration import build_phase2_dataset, migrate_phase1_seed_dataset


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
            "provenance_id": "fixture-legitimate-synthetic",
            "license": "project-generated",
            "pii_reviewed": True,
            "reviewer": "Test fixture review",
            "notes": "Test fixture.",
        },
    ]


def _frame():
    return pd.DataFrame(_valid_rows(), columns=REQUIRED_COLUMNS)


def _provenance_frame():
    return pd.DataFrame(
        [
            {
                "provenance_id": "phase1-seed-synthetic",
                "source_name": "Phase 1 seed dataset",
                "source_type": "synthetic",
                "collection_method": "Project-authored synthetic examples",
                "license": "project-generated",
                "pii_reviewed": True,
                "reviewer": "Phase 1 manual review",
                "allowed_labels": "|".join(sorted(TRAINED_LABELS - {"legitimate"})),
                "sha256": "d6e45c9d4cebd4d8a6228833a810aecdd11207c15a1d41646b015e93fe7c3179",
                "notes": "Existing Phase 1 synthetic batch.",
            },
            {
                "provenance_id": "fixture-legitimate-synthetic",
                "source_name": "Synthetic legitimate test fixture",
                "source_type": "synthetic",
                "collection_method": "Test-only project-authored fixture",
                "license": "project-generated",
                "pii_reviewed": True,
                "reviewer": "Test fixture review",
                "allowed_labels": "legitimate",
                "sha256": "",
                "notes": "Not part of the Phase 1 training seed.",
            },
        ],
        columns=PROVENANCE_REQUIRED_COLUMNS,
    )


def test_load_phase2_dataset_reads_csv_and_validates_it(tmp_path):
    dataset_path = tmp_path / "phase2.csv"
    _frame().to_csv(dataset_path, index=False)

    loaded = load_phase2_dataset(dataset_path)

    assert list(loaded.columns) == list(REQUIRED_COLUMNS)
    assert len(loaded) == 2


def test_validate_phase2_dataset_returns_immutable_summary_with_counts():
    summary = validate_phase2_dataset(_frame(), _provenance_frame(), minimum_per_label=0)

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


@pytest.mark.parametrize("value", [False, "false"])
def test_rejects_rows_without_confirmed_pii_review(value):
    frame = _frame()
    frame["pii_reviewed"] = frame["pii_reviewed"].astype(object)
    frame.loc[0, "pii_reviewed"] = value

    with pytest.raises(ValueError, match="unreviewed PII"):
        validate_phase2_dataset(frame)


@pytest.mark.parametrize("value", ["no", 0, None])
def test_rejects_invalid_pii_review_boolean(value):
    frame = _frame()
    frame["pii_reviewed"] = frame["pii_reviewed"].astype(object)
    frame.loc[0, "pii_reviewed"] = value

    with pytest.raises(ValueError, match="invalid boolean"):
        validate_phase2_dataset(frame)


def test_rejects_template_group_crossing_splits():
    frame = _frame()
    frame.loc[1, "template_group"] = frame.loc[0, "template_group"]

    with pytest.raises(ValueError, match="template_group.*crosses splits"):
        validate_phase2_dataset(frame)


def test_rejects_missing_provenance_ids_when_provenance_is_supplied():
    provenance = _provenance_frame()
    provenance.loc[:, "provenance_id"] = ["another-source-one", "another-source-two"]

    with pytest.raises(ValueError, match="missing provenance IDs"):
        validate_phase2_dataset(_frame(), provenance)


@pytest.mark.parametrize("column, value", [
    ("source_type", "external"),
    ("license", "unknown-license"),
    ("reviewer", "Someone else"),
    ("pii_reviewed", False),
])
def test_rejects_dataset_metadata_that_contradicts_provenance(column, value):
    frame = _frame()
    frame[column] = frame[column].astype(object)
    frame.loc[0, column] = value

    with pytest.raises(ValueError, match="contradicts provenance|unreviewed PII"):
        validate_phase2_dataset(frame, _provenance_frame(), minimum_per_label=0)


def test_rejects_label_outside_provenance_scope():
    frame = _frame()
    frame.loc[0, "label"] = "legitimate"

    with pytest.raises(ValueError, match="not allowed by provenance"):
        validate_phase2_dataset(frame, _provenance_frame(), minimum_per_label=0)


@pytest.mark.parametrize("column", ["id", "source_type", "language_mix", "template_group", "provenance_id", "license", "reviewer", "notes"])
def test_rejects_blank_identifiers_and_metadata(column):
    frame = _frame()
    frame.loc[0, column] = " "

    with pytest.raises(ValueError, match="blank"):
        validate_phase2_dataset(frame, _provenance_frame(), minimum_per_label=0)


def test_rejects_malformed_or_duplicate_provenance_records():
    malformed = _provenance_frame()
    malformed.loc[0, "allowed_labels"] = "upi_refund_scam|not_a_label"
    with pytest.raises(ValueError, match="invalid allowed_labels"):
        validate_phase2_dataset(_frame(), malformed, minimum_per_label=0)

    duplicate = _provenance_frame()
    duplicate.loc[1, "provenance_id"] = duplicate.loc[0, "provenance_id"]
    with pytest.raises(ValueError, match="duplicate provenance_id"):
        validate_phase2_dataset(_frame(), duplicate, minimum_per_label=0)


def test_load_uses_repository_provenance_register_and_enforces_label_scope(tmp_path):
    dataset_path = tmp_path / "phase2.csv"
    invalid = _frame()
    invalid.loc[1, "provenance_id"] = "phase1-seed-synthetic"
    invalid.loc[1, "reviewer"] = "Phase 1 manual review"
    invalid.to_csv(dataset_path, index=False)

    with pytest.raises(ValueError, match="not allowed by provenance"):
        load_phase2_dataset(dataset_path)


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
    summary = validate_phase2_dataset(first, _provenance_frame(), minimum_per_label=0)
    assert len(first) == 64
    assert "legitimate" not in set(first["label"])
    assert set(first["source_type"]) == {"synthetic"}
    assert set(first["reviewer"]) == {"Phase 1 manual review"}
    assert summary.meets_phase2_target is False
    assert set(first["split"]) <= {"train", "validation", "test"}
    assert set(first["label"]) == set(TRAINED_LABELS) - {"legitimate"}


def test_phase1_migration_rejects_modified_source_but_allows_identical_copy(tmp_path):
    project_root = Path(__file__).resolve().parents[1]
    source_path = project_root / "data" / "samples" / "phase1_seed_dataset.csv"
    copied_source = tmp_path / "identical.csv"
    copied_source.write_bytes(source_path.read_bytes())

    migrate_phase1_seed_dataset(copied_source, tmp_path / "from-copy.csv")

    copied_source.write_bytes(copied_source.read_bytes() + b"\n")
    with pytest.raises(ValueError, match="canonical Phase 1 seed"):
        migrate_phase1_seed_dataset(copied_source, tmp_path / "modified.csv")


def test_phase1_family_and_split_mapping_is_independent_of_input_order():
    project_root = Path(__file__).resolve().parents[1]
    source = pd.read_csv(project_root / "data" / "samples" / "phase1_seed_dataset.csv")

    original = build_phase2_dataset(source)
    shuffled = build_phase2_dataset(source.sample(frac=1, random_state=7))
    original_mapping = original.set_index("id")[["template_group", "split"]].sort_index()
    shuffled_mapping = shuffled.set_index("id")[["template_group", "split"]].sort_index()

    pd.testing.assert_frame_equal(original_mapping, shuffled_mapping)
    assert original_mapping.loc[49, "template_group"] == original_mapping.loc[50, "template_group"]
    assert original.groupby("template_group")["split"].nunique().eq(1).all()
    assert original.groupby("template_group").size().max() > 1
