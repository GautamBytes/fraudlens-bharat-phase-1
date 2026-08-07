"""Dataset contract for honest Phase 2 training data."""

from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Mapping, Optional, Union

import pandas as pd

from fraudlens.preprocessing import normalize_text


REQUIRED_COLUMNS = (
    "id",
    "text",
    "label",
    "source_type",
    "language_mix",
    "template_group",
    "split",
    "provenance_id",
    "license",
    "pii_reviewed",
    "reviewer",
    "notes",
)

TRAINED_LABELS = frozenset(
    {
        "kyc_scam",
        "digital_arrest",
        "fake_job",
        "investment_scam",
        "loan_scam",
        "courier_scam",
        "upi_refund_scam",
        "otp_phishing",
        "legitimate",
    }
)

ALLOWED_SPLITS = frozenset({"train", "validation", "test"})
PHASE2_TARGET_PER_LABEL = 200


@dataclass(frozen=True)
class DatasetSummary:
    """Read-only counts and target status for a validated dataset."""

    row_count: int
    label_counts: Mapping[str, int]
    split_counts: Mapping[str, int]
    source_type_counts: Mapping[str, int]
    meets_phase2_target: bool


def load_phase2_dataset(path: Union[str, Path]) -> pd.DataFrame:
    """Load a Phase 2 CSV without changing its recorded values."""
    return pd.read_csv(Path(path))


def validate_phase2_dataset(
    frame: pd.DataFrame,
    provenance_frame: Optional[pd.DataFrame] = None,
    minimum_per_label: int = 1,
) -> DatasetSummary:
    """Validate a Phase 2 dataset and return an immutable summary."""
    if minimum_per_label < 0:
        raise ValueError("minimum_per_label must be non-negative")

    missing_columns = [column for column in REQUIRED_COLUMNS if column not in frame.columns]
    if missing_columns:
        raise ValueError("dataset missing required columns: {}".format(", ".join(missing_columns)))

    if frame["id"].duplicated().any():
        raise ValueError("dataset contains duplicate id values")

    normalized_texts = frame["text"].map(normalize_text)
    if normalized_texts.eq("").any():
        raise ValueError("dataset contains empty text")
    if normalized_texts.duplicated().any():
        raise ValueError("dataset contains duplicate normalized text")

    invalid_labels = _invalid_values(frame["label"], TRAINED_LABELS)
    if invalid_labels:
        raise ValueError("dataset contains invalid label values: {}".format(", ".join(invalid_labels)))

    invalid_splits = _invalid_values(frame["split"], ALLOWED_SPLITS)
    if invalid_splits:
        raise ValueError("dataset contains invalid split values: {}".format(", ".join(invalid_splits)))

    if not frame["pii_reviewed"].map(_is_confirmed_pii_review).all():
        raise ValueError("dataset contains unreviewed PII")

    split_counts_by_template = frame.groupby("template_group", dropna=False)["split"].nunique(dropna=False)
    if (split_counts_by_template > 1).any():
        raise ValueError("template_group crosses splits")

    if provenance_frame is not None:
        if "provenance_id" not in provenance_frame.columns:
            raise ValueError("provenance frame missing provenance_id column")
        known_provenance_ids = set(provenance_frame["provenance_id"].dropna().astype(str))
        missing_provenance_ids = sorted(
            set(frame["provenance_id"].dropna().astype(str)) - known_provenance_ids
        )
        if frame["provenance_id"].isna().any():
            missing_provenance_ids.append("<empty>")
        if missing_provenance_ids:
            raise ValueError(
                "dataset contains missing provenance IDs: {}".format(
                    ", ".join(missing_provenance_ids)
                )
            )

    label_counts = _counts(frame["label"])
    for label in TRAINED_LABELS:
        if label_counts.get(label, 0) < minimum_per_label:
            raise ValueError(
                "dataset does not satisfy minimum_per_label={}".format(minimum_per_label)
            )

    return DatasetSummary(
        row_count=len(frame),
        label_counts=MappingProxyType(label_counts),
        split_counts=MappingProxyType(_counts(frame["split"])),
        source_type_counts=MappingProxyType(_counts(frame["source_type"])),
        meets_phase2_target=all(
            label_counts.get(label, 0) >= PHASE2_TARGET_PER_LABEL for label in TRAINED_LABELS
        ),
    )


def _invalid_values(values: pd.Series, allowed_values: frozenset) -> list:
    return sorted({str(value) for value in values if value not in allowed_values})


def _is_confirmed_pii_review(value: object) -> bool:
    return str(value).strip().lower() == "true"


def _counts(values: pd.Series) -> dict:
    return {str(key): int(value) for key, value in values.value_counts().sort_index().items()}
