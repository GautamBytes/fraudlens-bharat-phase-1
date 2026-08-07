"""Dataset contract and provenance enforcement for Phase 2 training data."""

from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Dict, Mapping, Optional, Set, Union

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
PROVENANCE_REQUIRED_COLUMNS = (
    "provenance_id",
    "source_name",
    "source_type",
    "collection_method",
    "license",
    "pii_reviewed",
    "reviewer",
    "allowed_labels",
    "sha256",
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
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PROVENANCE_PATH = _PROJECT_ROOT / "data" / "provenance" / "phase2_sources.csv"
_DATASET_NONBLANK_COLUMNS = (
    "id",
    "source_type",
    "language_mix",
    "template_group",
    "split",
    "provenance_id",
    "license",
    "reviewer",
    "notes",
)
_PROVENANCE_NONBLANK_COLUMNS = tuple(
    column for column in PROVENANCE_REQUIRED_COLUMNS if column != "sha256"
)


@dataclass(frozen=True)
class DatasetSummary:
    """Read-only counts and target status for a validated dataset."""

    row_count: int
    label_counts: Mapping[str, int]
    split_counts: Mapping[str, int]
    source_type_counts: Mapping[str, int]
    meets_phase2_target: bool


def load_phase2_dataset(
    path: Union[str, Path],
    provenance_path: Optional[Union[str, Path]] = None,
    minimum_per_label: int = 0,
) -> pd.DataFrame:
    """Load and validate a dataset against the repository provenance register."""
    frame = pd.read_csv(Path(path))
    provenance = load_phase2_provenance(provenance_path)
    validate_phase2_dataset(frame, provenance, minimum_per_label)
    return frame


def load_phase2_provenance(path: Optional[Union[str, Path]] = None) -> pd.DataFrame:
    """Load the authoritative Phase 2 provenance register."""
    return pd.read_csv(Path(path) if path is not None else DEFAULT_PROVENANCE_PATH)


def validate_phase2_dataset(
    frame: pd.DataFrame,
    provenance_frame: Optional[pd.DataFrame] = None,
    minimum_per_label: int = 1,
) -> DatasetSummary:
    """Validate dataset rows and their full provenance metadata."""
    if minimum_per_label < 0:
        raise ValueError("minimum_per_label must be non-negative")

    _require_columns(frame, REQUIRED_COLUMNS, "dataset")
    _reject_blank_values(frame, _DATASET_NONBLANK_COLUMNS, "dataset")
    if frame["id"].duplicated().any():
        raise ValueError("dataset contains duplicate id values")

    normalized_texts = frame["text"].map(_normalize_or_empty)
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

    dataset_pii = _parse_boolean_column(frame["pii_reviewed"], "dataset pii_reviewed")
    if not dataset_pii.all():
        raise ValueError("dataset contains unreviewed PII")

    split_counts_by_template = frame.groupby("template_group", dropna=False)["split"].nunique(dropna=False)
    if (split_counts_by_template > 1).any():
        raise ValueError("template_group crosses splits")

    provenance = provenance_frame if provenance_frame is not None else load_phase2_provenance()
    provenance_by_id, allowed_labels = _validate_provenance(provenance)
    _enforce_provenance(frame, dataset_pii, provenance_by_id, allowed_labels)

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


def _require_columns(frame: pd.DataFrame, required_columns: tuple, name: str) -> None:
    missing_columns = [column for column in required_columns if column not in frame.columns]
    if missing_columns:
        raise ValueError("{} missing required columns: {}".format(name, ", ".join(missing_columns)))


def _reject_blank_values(frame: pd.DataFrame, columns: tuple, name: str) -> None:
    for column in columns:
        values = frame[column]
        if values.isna().any() or values.map(lambda value: not str(value).strip()).any():
            raise ValueError("{} contains blank {} values".format(name, column))


def _normalize_or_empty(value: object) -> str:
    return normalize_text(value) if isinstance(value, str) else ""


def _invalid_values(values: pd.Series, allowed_values: Set[str]) -> list:
    return sorted({str(value) for value in values if value not in allowed_values})


def _parse_boolean_column(values: pd.Series, name: str) -> pd.Series:
    parsed = values.map(_parse_boolean)
    if parsed.isna().any():
        raise ValueError("{} contains invalid boolean values".format(name))
    return parsed.astype(bool)


def _parse_boolean(value: object) -> Optional[bool]:
    normalized = str(value).strip().lower()
    if normalized == "true":
        return True
    if normalized == "false":
        return False
    return None


def _validate_provenance(provenance: pd.DataFrame) -> tuple:
    _require_columns(provenance, PROVENANCE_REQUIRED_COLUMNS, "provenance")
    _reject_blank_values(provenance, _PROVENANCE_NONBLANK_COLUMNS, "provenance")
    if provenance["provenance_id"].duplicated().any():
        raise ValueError("provenance contains duplicate provenance_id values")

    validated = provenance.copy()
    validated["pii_reviewed"] = _parse_boolean_column(
        validated["pii_reviewed"], "provenance pii_reviewed"
    )
    allowed_labels = {}
    for _, source in validated.iterrows():
        source_id = str(source["provenance_id"])
        source_labels = _parse_allowed_labels(source["allowed_labels"])
        if not source_labels:
            raise ValueError("provenance contains invalid allowed_labels values")
        allowed_labels[source_id] = source_labels

    return validated.set_index("provenance_id", drop=False), allowed_labels


def _parse_allowed_labels(value: object) -> Set[str]:
    labels = {label.strip() for label in str(value).split("|") if label.strip()}
    if not labels or not labels.issubset(TRAINED_LABELS):
        raise ValueError("provenance contains invalid allowed_labels values")
    return labels


def _enforce_provenance(
    frame: pd.DataFrame,
    dataset_pii: pd.Series,
    provenance_by_id: pd.DataFrame,
    allowed_labels: Dict[str, Set[str]],
) -> None:
    missing_ids = sorted(set(frame["provenance_id"].astype(str)) - set(provenance_by_id.index))
    if missing_ids:
        raise ValueError("dataset contains missing provenance IDs: {}".format(", ".join(missing_ids)))

    for index, row in frame.iterrows():
        source_id = str(row["provenance_id"])
        source = provenance_by_id.loc[source_id]
        if row["label"] not in allowed_labels[source_id]:
            raise ValueError("dataset label is not allowed by provenance")
        if (
            row["source_type"] != source["source_type"]
            or row["license"] != source["license"]
            or row["reviewer"] != source["reviewer"]
            or dataset_pii.loc[index] != source["pii_reviewed"]
        ):
            raise ValueError("dataset metadata contradicts provenance")


def _counts(values: pd.Series) -> dict:
    return {str(key): int(value) for key, value in values.value_counts().sort_index().items()}
