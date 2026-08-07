"""Deterministically bootstrap Phase 2 from the registered Phase 1 seed."""

import argparse
import hashlib
import re
from pathlib import Path
from typing import Dict, List, Tuple, Union

import pandas as pd

from fraudlens.data_contract import (
    REQUIRED_COLUMNS,
    load_phase2_provenance,
    validate_phase2_dataset,
)
from fraudlens.preprocessing import normalize_text


_PHASE1_REQUIRED_COLUMNS = ("id", "text", "label", "source_type", "language_mix", "notes")
_PROVENANCE_ID = "phase1-seed-synthetic"


def migrate_phase1_seed_dataset(
    source_path: Union[str, Path], destination_path: Union[str, Path]
) -> Path:
    """Migrate only a byte-identical copy of the registered Phase 1 seed."""
    source = Path(source_path)
    destination = Path(destination_path)
    provenance = load_phase2_provenance()
    source_record = _registered_seed_record(provenance)
    _verify_canonical_seed(source, source_record["sha256"])

    phase1 = pd.read_csv(source)
    grouped = derive_phase1_group_split_mapping(phase1)
    assignments = grouped.set_index("id")
    records: List[dict] = []
    for _, row in phase1.iterrows():
        record = row.to_dict()
        assignment = assignments.loc[row["id"]]
        record.update(
            {
                "template_group": assignment["template_group"],
                "split": assignment["split"],
                "provenance_id": _PROVENANCE_ID,
                "license": source_record["license"],
                "pii_reviewed": source_record["pii_reviewed"],
                "reviewer": source_record["reviewer"],
            }
        )
        records.append(record)
    migrated = pd.DataFrame(records, columns=REQUIRED_COLUMNS)
    validate_phase2_dataset(migrated, provenance, minimum_per_label=0)
    destination.parent.mkdir(parents=True, exist_ok=True)
    migrated.to_csv(destination, index=False)
    return destination


def derive_phase1_group_split_mapping(phase1: pd.DataFrame) -> pd.DataFrame:
    """Derive non-provenance family and split metadata from Phase 1 annotations.

    The Phase 1 seed has no explicit template-family column.  We retain the
    normalized annotation key for most rows, which is the least speculative
    available family evidence.  A narrow collect-request mechanism key joins the
    two UPI variants whose text and annotations describe the same action.  This
    helper intentionally returns no source, reviewer, licence, or PII claims.
    """
    _require_phase1_columns(phase1)
    grouped_rows = []
    group_sizes: Dict[str, Dict[str, int]] = {}
    for _, row in phase1.iterrows():
        template_group = derive_template_group(row["label"], row["text"], row["notes"])
        label = str(row["label"])
        sizes = group_sizes.setdefault(label, {})
        sizes[template_group] = sizes.get(template_group, 0) + 1
        grouped_rows.append(
            {"id": row["id"], "label": label, "template_group": template_group}
        )

    split_by_group = {}
    for label, sizes in group_sizes.items():
        split_by_group.update(_assign_label_splits(label, sizes))
    for row in grouped_rows:
        row["split"] = split_by_group[row["template_group"]]
    return pd.DataFrame(grouped_rows, columns=("id", "label", "template_group", "split"))


def derive_template_group(label: str, text: str, notes: str) -> str:
    """Return a stable family key from recorded Phase 1 mechanism/annotation text."""
    evidence = "{} {}".format(normalize_text(text), normalize_text(notes))
    if label == "upi_refund_scam" and (
        "collect request" in evidence or "request accept" in evidence
    ):
        family_key = "collect-request"
    else:
        family_key = _normalized_note_key(notes)
    return "{}-{}".format(label, family_key)


def _normalized_note_key(notes: str) -> str:
    key = re.sub(r"[^a-z0-9]+", "-", normalize_text(notes)).strip("-")
    return key or "unannotated"


def _assign_label_splits(label: str, group_sizes: Dict[str, int]) -> Dict[str, str]:
    """Allocate stable template groups while keeping every available label evaluable."""
    groups = sorted(group_sizes, key=lambda group: _stable_group_key(label, group))
    assignments = {group: "train" for group in groups}
    if len(groups) >= 3:
        # Reserve the smallest groups for evaluation so an eight-row label with
        # a paired family still retains roughly six rows for training.
        evaluation_groups = sorted(
            groups, key=lambda group: (group_sizes[group], _stable_group_key(label, group))
        )[:2]
        assignments[evaluation_groups[0]] = "validation"
        assignments[evaluation_groups[1]] = "test"
    elif len(groups) == 2:
        assignments[groups[1]] = "validation"
    return assignments


def _stable_group_key(label: str, group: str) -> Tuple[str, str]:
    digest = hashlib.sha256("{}\0{}".format(label, group).encode("utf-8")).hexdigest()
    return digest, group


def _require_phase1_columns(phase1: pd.DataFrame) -> None:
    missing_columns = set(_PHASE1_REQUIRED_COLUMNS) - set(phase1.columns)
    if missing_columns:
        raise ValueError("phase 1 dataset missing columns: {}".format(", ".join(sorted(missing_columns))))


def _registered_seed_record(provenance: pd.DataFrame) -> pd.Series:
    records = provenance[provenance["provenance_id"] == _PROVENANCE_ID]
    if len(records) != 1:
        raise ValueError("provenance must contain one registered Phase 1 seed record")
    record = records.iloc[0]
    if not str(record["sha256"]).strip():
        raise ValueError("registered Phase 1 seed record must include sha256")
    return record


def _verify_canonical_seed(source: Path, expected_digest: object) -> None:
    actual_digest = hashlib.sha256(source.read_bytes()).hexdigest()
    if actual_digest != str(expected_digest).strip().lower():
        raise ValueError("source is not the canonical Phase 1 seed content")


def main() -> None:
    project_root = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source",
        type=Path,
        default=project_root / "data" / "samples" / "phase1_seed_dataset.csv",
    )
    parser.add_argument(
        "--destination",
        type=Path,
        default=project_root / "data" / "samples" / "phase2_dataset.csv",
    )
    args = parser.parse_args()
    print(migrate_phase1_seed_dataset(args.source, args.destination))


if __name__ == "__main__":
    main()
