import hashlib
import json
import zipfile
from io import BytesIO

import pytest

from fraudlens.external_evaluation import (
    ExternalSmsRow,
    grouped_stratified_split,
    load_uci_sms_archive,
    paired_stratified_bootstrap,
    run_external_evaluation,
    wilson_interval,
)
from fraudlens.prediction import Prediction


def _archive(rows: list[tuple[str, str]]) -> bytes:
    payload = "".join(f"{label}\t{text}\n" for label, text in rows).encode("utf-8")
    stream = BytesIO()
    with zipfile.ZipFile(stream, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("SMSSpamCollection", payload)
    return stream.getvalue()


def test_loader_requires_pinned_archive_hash_and_expected_contract(tmp_path):
    archive_bytes = _archive([("ham", "Hello"), ("spam", "WIN now")])
    path = tmp_path / "sms.zip"
    path.write_bytes(archive_bytes)

    rows = load_uci_sms_archive(
        path,
        expected_sha256=hashlib.sha256(archive_bytes).hexdigest(),
        expected_rows=2,
    )

    assert rows == (
        ExternalSmsRow(label="ham", text="Hello"),
        ExternalSmsRow(label="spam", text="WIN now"),
    )
    with pytest.raises(ValueError, match="checksum"):
        load_uci_sms_archive(path, expected_sha256="0" * 64, expected_rows=2)
    with pytest.raises(ValueError, match="row count"):
        load_uci_sms_archive(
            path,
            expected_sha256=hashlib.sha256(archive_bytes).hexdigest(),
            expected_rows=3,
        )


def test_grouped_split_is_deterministic_stratified_and_duplicate_safe():
    rows = tuple(
        ExternalSmsRow(label=label, text=text)
        for label in ("ham", "spam")
        for index in range(20)
        for text in ([f"{label} sample {index}"] * (2 if index == 0 else 1))
    )

    first = grouped_stratified_split(rows, seed=42)
    second = grouped_stratified_split(tuple(reversed(rows)), seed=42)

    assert first.manifest_sha256 == second.manifest_sha256
    assert first.counts == second.counts
    assert set(first.rows) == {"train", "validation", "test"}
    assert all({row.label for row in split} == {"ham", "spam"} for split in first.rows.values())
    normalized_memberships: dict[str, set[str]] = {}
    for split_name, split_rows in first.rows.items():
        for row in split_rows:
            normalized_memberships.setdefault(row.text.casefold(), set()).add(split_name)
    assert all(len(splits) == 1 for splits in normalized_memberships.values())


def test_grouped_split_rejects_cross_label_duplicate_text():
    with pytest.raises(ValueError, match="conflicting labels"):
        grouped_stratified_split(
            (
                ExternalSmsRow(label="ham", text="Same Message"),
                ExternalSmsRow(label="spam", text="same   message"),
            )
        )


def test_uncertainty_helpers_are_deterministic_and_bounded():
    lower, upper = wilson_interval(80, 100)
    assert lower == pytest.approx(0.71117083)
    assert upper == pytest.approx(0.86663307)

    comparison = paired_stratified_bootstrap(
        ["ham", "ham", "spam", "spam"],
        ["ham", "ham", "spam", "ham"],
        ["ham", "spam", "spam", "spam"],
        samples=200,
        seed=42,
    )
    assert comparison == paired_stratified_bootstrap(
        ["ham", "ham", "spam", "spam"],
        ["ham", "ham", "spam", "ham"],
        ["ham", "spam", "spam", "spam"],
        samples=200,
        seed=42,
    )
    assert set(comparison) == {
        "samples",
        "macro_f1_difference",
        "confidence_interval_95",
        "probability_candidate_b_better",
    }
    assert -1 <= comparison["confidence_interval_95"][0] <= 1
    assert -1 <= comparison["confidence_interval_95"][1] <= 1


def test_aggregate_report_contract_cannot_contain_messages_or_row_predictions(tmp_path):
    archive_bytes = _archive(
        [("ham", f"ordinary message {index}") for index in range(12)]
        + [("spam", f"prize offer {index}") for index in range(12)]
    )
    path = tmp_path / "sms.zip"
    path.write_bytes(archive_bytes)
    rows = load_uci_sms_archive(
        path,
        expected_sha256=hashlib.sha256(archive_bytes).hexdigest(),
        expected_rows=24,
    )
    split = grouped_stratified_split(rows)
    serialized = json.dumps(split.public_metadata(), sort_keys=True)

    assert "ordinary message" not in serialized
    assert "prize offer" not in serialized
    assert "predictions" not in serialized
    assert set(split.public_metadata()) == {
        "rows",
        "labels",
        "normalized_groups",
        "duplicate_rows",
        "split_rows",
        "split_labels",
        "group_to_split_manifest_sha256",
    }


class _HamStressPredictor:
    def predict(self, text: str) -> Prediction:
        if "meeting" in text:
            return Prediction("unknown", 0.3, "test", "test-v1", True)
        return Prediction("kyc_scam", 0.7, "test", "test-v1", False)


def test_external_benchmark_writes_only_aggregate_reproducible_evidence(tmp_path):
    archive_rows = []
    for index in range(40):
        archive_rows.append(("ham", f"family meeting schedule number {index}"))
        archive_rows.append(("spam", f"win a cash prize offer number {index}"))
    archive_bytes = _archive(archive_rows)
    archive_path = tmp_path / "sms.zip"
    archive_path.write_bytes(archive_bytes)
    expected_hash = hashlib.sha256(archive_bytes).hexdigest()

    first = tmp_path / "first"
    second = tmp_path / "second"
    report = run_external_evaluation(
        archive_path,
        first,
        expected_sha256=expected_hash,
        expected_rows=80,
        bootstrap_samples=100,
        predictor=_HamStressPredictor(),
    )
    run_external_evaluation(
        archive_path,
        second,
        expected_sha256=expected_hash,
        expected_rows=80,
        bootstrap_samples=100,
        predictor=_HamStressPredictor(),
    )

    assert (first / "external_sms_summary.json").read_bytes() == (
        second / "external_sms_summary.json"
    ).read_bytes()
    assert (first / "external_sms_models.csv").read_bytes() == (
        second / "external_sms_models.csv"
    ).read_bytes()
    assert set(report["models"]) == {
        "word_tfidf_logistic_regression",
        "character_tfidf_logistic_regression",
        "calibrated_character_tfidf",
    }
    assert report["dataset"]["raw_messages_committed"] is False
    assert report["dataset"]["row_predictions_committed"] is False
    assert report["runtime_ham_stress"]["support"] > 0
    assert report["runtime_ham_stress"]["interpretation"] == (
        "Stress test on held-out ham only; this is not legitimate-class accuracy."
    )
    serialized = json.dumps(report, sort_keys=True)
    assert "family meeting schedule" not in serialized
    assert "win a cash prize" not in serialized
    for model in report["models"].values():
        assert set(model["test"]["confidence_intervals_95"]) == {
            "accuracy",
            "spam_recall",
            "ham_specificity",
        }
