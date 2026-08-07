"""Deterministically bootstrap the Phase 2 contract from the Phase 1 seed."""

import argparse
from pathlib import Path
from typing import Union

import pandas as pd

from fraudlens.data_contract import REQUIRED_COLUMNS


_PHASE1_REQUIRED_COLUMNS = ("id", "text", "label", "source_type", "language_mix", "notes")
_SPLITS = ("train", "train", "train", "train", "train", "train", "validation", "test")
_PROVENANCE_ID = "phase1-seed-synthetic"
_LICENSE = "project-generated"
_REVIEWER = "Phase 1 manual review"


def migrate_phase1_seed_dataset(
    source_path: Union[str, Path], destination_path: Union[str, Path]
) -> Path:
    """Map the 64-row Phase 1 synthetic seed into the Phase 2 CSV schema."""
    source = Path(source_path)
    destination = Path(destination_path)
    phase1 = pd.read_csv(source)
    missing_columns = set(_PHASE1_REQUIRED_COLUMNS) - set(phase1.columns)
    if missing_columns:
        raise ValueError("phase 1 dataset missing columns: {}".format(", ".join(sorted(missing_columns))))

    records = []
    label_positions = {}
    for _, row in phase1.iterrows():
        record = row.to_dict()
        label = record["label"]
        position = label_positions.get(label, 0)
        label_positions[label] = position + 1
        record.update(
            {
                "template_group": "{}-phase1-{:02d}".format(label, position + 1),
                "split": _SPLITS[position % len(_SPLITS)],
                "provenance_id": _PROVENANCE_ID,
                "license": _LICENSE,
                "pii_reviewed": True,
                "reviewer": _REVIEWER,
            }
        )
        records.append(record)

    migrated = pd.DataFrame(records, columns=REQUIRED_COLUMNS)
    destination.parent.mkdir(parents=True, exist_ok=True)
    migrated.to_csv(destination, index=False)
    return destination


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
