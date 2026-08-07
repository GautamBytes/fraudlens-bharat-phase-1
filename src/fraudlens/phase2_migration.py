"""Deterministically bootstrap Phase 2 from the registered Phase 1 seed."""

import argparse
import hashlib
from pathlib import Path
from typing import Dict, Union

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

    migrated = build_phase2_dataset(pd.read_csv(source), source_record)
    validate_phase2_dataset(migrated, provenance, minimum_per_label=0)
    destination.parent.mkdir(parents=True, exist_ok=True)
    migrated.to_csv(destination, index=False)
    return destination


def build_phase2_dataset(
    phase1: pd.DataFrame, source_record: pd.Series = None
) -> pd.DataFrame:
    """Create stable Phase 2 rows from canonical Phase 1 content.

    Phase 1 has no explicit family column.  Family keys therefore use the recorded
    label plus recurring message/annotation mechanisms, never row order or IDs.
    This conservatively keeps close variants together for split assignment.
    """
    missing_columns = set(_PHASE1_REQUIRED_COLUMNS) - set(phase1.columns)
    if missing_columns:
        raise ValueError("phase 1 dataset missing columns: {}".format(", ".join(sorted(missing_columns))))
    if source_record is None:
        source_record = _registered_seed_record(load_phase2_provenance())

    records = []
    for _, row in phase1.iterrows():
        record = row.to_dict()
        template_group = derive_template_group(record["label"], record["text"], record["notes"])
        record.update(
            {
                "template_group": template_group,
                "split": _split_for_template_group(template_group),
                "provenance_id": _PROVENANCE_ID,
                "license": source_record["license"],
                "pii_reviewed": source_record["pii_reviewed"],
                "reviewer": source_record["reviewer"],
            }
        )
        records.append(record)
    return pd.DataFrame(records, columns=REQUIRED_COLUMNS)


def derive_template_group(label: str, text: str, notes: str) -> str:
    """Return a content-derived family key for related Phase 1 variants."""
    evidence = "{} {}".format(normalize_text(text), normalize_text(notes))
    family = _family_for(label, evidence)
    return "{}-{}".format(label, family)


def _family_for(label: str, evidence: str) -> str:
    # The rules encode observable, repeated scam mechanisms in Phase 1 text/notes.
    # They are deliberately broad when uncertain: grouping too much is safer than
    # allowing paraphrases of the same mechanism to leak across evaluation splits.
    if label == "kyc_scam":
        return "account-access" if _contains_any(evidence, ("block", "freeze", "suspension", "disable", "hold")) else "verification-request"
    if label == "digital_arrest":
        return "remote-coercion" if _contains_any(evidence, ("video", "camera", "monitor")) else "case-settlement"
    if label == "fake_job":
        return "registration-fee" if _contains_any(evidence, ("registration", "joining", "fee", "charge", "deposit")) else "work-offer"
    if label == "investment_scam":
        return "guaranteed-return" if _contains_any(evidence, ("guaranteed", "double", "2x", "fixed income", "zero risk")) else "paid-access"
    if label == "loan_scam":
        return "advance-fee" if _contains_any(evidence, ("fee", "charge", "insurance", "gst", "processing")) else "coercive-or-credential"
    if label == "courier_scam":
        return "law-enforcement" if _contains_any(evidence, ("fir", "drugs", "illegal", "customs", "police")) else "delivery-update"
    if label == "upi_refund_scam":
        return "payment-authorization" if _contains_any(evidence, ("collect", "accept", "approve", "scan qr", "upi pin")) else "refund-promise"
    if label == "otp_phishing":
        return "account-credential" if _contains_any(evidence, ("password", "login", "account", "telegram")) else "payment-credential"
    return "unclassified"


def _contains_any(evidence: str, markers: tuple) -> bool:
    return any(marker in evidence for marker in markers)


def _split_for_template_group(template_group: str) -> str:
    bucket = int(hashlib.sha256(template_group.encode("utf-8")).hexdigest()[:8], 16) % 100
    if bucket < 70:
        return "train"
    if bucket < 85:
        return "validation"
    return "test"


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
