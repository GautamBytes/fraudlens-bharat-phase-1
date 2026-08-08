"""Deterministic dataset auditing for the academic research benchmark."""

from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable, Sequence

from fraudlens.data_contract import PHASE2_TARGET_PER_LABEL, REQUIRED_COLUMNS, TRAINED_LABELS
from fraudlens.preprocessing import normalize_text


@dataclass(frozen=True)
class ResearchRow:
    id: str
    text: str
    label: str
    source_type: str
    language_mix: str
    template_group: str
    split: str
    provenance_id: str
    license: str
    pii_reviewed: str
    reviewer: str
    notes: str


@dataclass(frozen=True)
class DatasetAudit:
    row_count: int
    label_counts: dict[str, int]
    split_counts: dict[str, int]
    language_counts: dict[str, int]
    source_type_counts: dict[str, int]
    missing_labels: tuple[str, ...]
    meets_phase2_target: bool
    normalized_duplicate_groups: tuple[tuple[str, ...], ...]
    template_groups_crossing_splits: tuple[str, ...]
    provenance_ids_crossing_splits: tuple[str, ...]
    limitations: tuple[str, ...]


def load_research_rows(path: Path | str) -> tuple[ResearchRow, ...]:
    """Load the fixed research fields without changing dataset contents."""
    with Path(path).open(newline="", encoding="utf-8") as stream:
        reader = csv.DictReader(stream)
        columns = tuple(reader.fieldnames or ())
        missing = tuple(column for column in REQUIRED_COLUMNS if column not in columns)
        if missing:
            raise ValueError(
                "research dataset missing required columns: {}".format(", ".join(missing))
            )
        rows = tuple(
            ResearchRow(**{column: str(record[column]) for column in REQUIRED_COLUMNS})
            for record in reader
        )
    return rows


def audit_dataset(rows: Sequence[ResearchRow]) -> DatasetAudit:
    """Summarize balance, provenance, duplication, and split-leakage risks."""
    label_counts = _sorted_counts(row.label for row in rows)
    split_counts = _sorted_counts(row.split for row in rows)
    language_counts = _sorted_counts(row.language_mix for row in rows)
    source_type_counts = _sorted_counts(row.source_type for row in rows)

    normalized_groups: dict[str, list[str]] = defaultdict(list)
    for row in rows:
        normalized_groups[_duplicate_key(row.text)].append(row.id)
    duplicate_groups = tuple(
        sorted(
            (tuple(sorted(ids)) for ids in normalized_groups.values() if len(ids) > 1),
            key=lambda ids: ids,
        )
    )

    template_splits = _values_by_key(rows, "template_group", "split")
    provenance_splits = _values_by_key(rows, "provenance_id", "split")
    missing_labels = tuple(sorted(TRAINED_LABELS - set(label_counts)))
    meets_target = all(
        label_counts.get(label, 0) >= PHASE2_TARGET_PER_LABEL for label in TRAINED_LABELS
    )

    limitations = []
    if rows and set(source_type_counts) == {"synthetic"}:
        limitations.append("synthetic_only")
    if "legitimate" in missing_labels:
        limitations.append("missing_legitimate_label")
    if not meets_target:
        limitations.append("below_200_examples_per_label")
    present_labels = set(label_counts)
    test_by_label = Counter(row.label for row in rows if row.split == "test")
    if present_labels and all(test_by_label[label] == 1 for label in present_labels):
        limitations.append("frozen_test_has_one_row_per_present_label")

    return DatasetAudit(
        row_count=len(rows),
        label_counts=label_counts,
        split_counts=split_counts,
        language_counts=language_counts,
        source_type_counts=source_type_counts,
        missing_labels=missing_labels,
        meets_phase2_target=meets_target,
        normalized_duplicate_groups=duplicate_groups,
        template_groups_crossing_splits=_cross_split_keys(template_splits),
        provenance_ids_crossing_splits=_cross_split_keys(provenance_splits),
        limitations=tuple(limitations),
    )


def write_dataset_audit(audit: DatasetAudit, path: Path | str) -> None:
    """Write stable, reviewable JSON evidence."""
    payload = asdict(audit)
    payload["schema_version"] = 1
    payload["required_columns"] = list(REQUIRED_COLUMNS)
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def _sorted_counts(values: Iterable[str]) -> dict[str, int]:
    return dict(sorted(Counter(values).items()))


def _duplicate_key(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", normalize_text(text)).strip()


def _values_by_key(
    rows: Sequence[ResearchRow], key_name: str, value_name: str
) -> dict[str, set[str]]:
    values: dict[str, set[str]] = defaultdict(set)
    for row in rows:
        values[getattr(row, key_name)].add(getattr(row, value_name))
    return values


def _cross_split_keys(values: dict[str, set[str]]) -> tuple[str, ...]:
    return tuple(sorted(key for key, splits in values.items() if len(splits) > 1))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    write_dataset_audit(audit_dataset(load_research_rows(args.dataset)), args.output)


if __name__ == "__main__":
    main()
