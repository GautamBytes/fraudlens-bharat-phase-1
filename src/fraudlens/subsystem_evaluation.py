"""Deterministic synthetic subsystem benchmarks for the capstone evidence."""

from __future__ import annotations

import argparse
import csv
import io
import json
import re
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Iterable, Mapping, Sequence

from PIL import Image, ImageDraw, ImageFilter

from fraudlens.analysis_service import build_complaint_draft
from fraudlens.config import LABELS
from fraudlens.entity_extraction import extract_entities
from fraudlens.graph_analysis import EntityLink, build_entity_graph
from fraudlens.model_inference import ModelPredictor
from fraudlens.ocr import OcrService
from fraudlens.privacy import mask_entity, stable_entity_id
from fraudlens.schemas import Entity
from fraudlens.url_risk import analyze_url


_ENTITY_TYPES = (
    "phone",
    "upi_id",
    "email",
    "url",
    "money",
    "otp_like_code",
    "urgency_phrase",
    "threat_phrase",
)


def benchmark_entities() -> dict[str, object]:
    cases: list[tuple[str, set[tuple[str, str]]]] = []
    for index in range(5):
        cases.extend(
            [
                (f"Call 98765{index:05d}", {("phone", f"98765{index:05d}")}),
                (f"Send to demo{index}@upi", {("upi_id", f"demo{index}@upi")}),
                (f"Email demo{index}@example.com", {("email", f"demo{index}@example.com")}),
                (
                    f"Open https://portal{index}.example.test/path",
                    {("url", f"https://portal{index}.example.test/path")},
                ),
                (f"Deposit Rs {1000 + index}", {("money", f"Rs {1000 + index}")}),
                (f"Verification code {4100 + index}", {("otp_like_code", str(4100 + index))}),
                (f"Please respond urgent ref {index}", {("urgency_phrase", "urgent")}),
                (f"Account may freeze ref {index}", {("threat_phrase", "freeze")}),
            ]
        )
    true_positive = false_positive = false_negative = exact = 0
    per_type = {name: {"tp": 0, "fp": 0, "fn": 0} for name in _ENTITY_TYPES}
    for text, expected in cases:
        actual = {(entity.type, entity.value) for entity in extract_entities(text)}
        exact += actual == expected
        for entity_type in _ENTITY_TYPES:
            expected_type = {item for item in expected if item[0] == entity_type}
            actual_type = {item for item in actual if item[0] == entity_type}
            tp = len(expected_type & actual_type)
            fp = len(actual_type - expected_type)
            fn = len(expected_type - actual_type)
            per_type[entity_type]["tp"] += tp
            per_type[entity_type]["fp"] += fp
            per_type[entity_type]["fn"] += fn
            true_positive += tp
            false_positive += fp
            false_negative += fn
    return {
        "support": len(cases),
        "micro_precision": _ratio(true_positive, true_positive + false_positive),
        "micro_recall": _ratio(true_positive, true_positive + false_negative),
        "micro_f1": _f1(true_positive, false_positive, false_negative),
        "exact_case_accuracy": _ratio(exact, len(cases)),
        "per_type": {
            name: {
                "precision": _ratio(values["tp"], values["tp"] + values["fp"]),
                "recall": _ratio(values["tp"], values["tp"] + values["fn"]),
                "f1": _f1(values["tp"], values["fp"], values["fn"]),
                "support": values["tp"] + values["fn"],
            }
            for name, values in per_type.items()
        },
    }


def benchmark_urls() -> dict[str, object]:
    cases: list[tuple[str, set[str]]] = []
    for index in range(4):
        cases.extend(
            [
                (f"http://plain{index}.example.test/path", {"non_https_url"}),
                (f"https://bit.ly/demo{index}", {"shortened_url"}),
                (f"https://192.0.2.{index + 1}/path", {"ip_address_url"}),
                (f"https://portal{index}.example.test/verify", {"suspicious_url_keyword"}),
                (f"https://secure-login-{index}.example.test/path", {"hyphenated_domain", "suspicious_url_keyword"}),
            ]
        )
    cases.extend(
        (f"https://docs{index}.example.org/reference", set()) for index in range(20)
    )
    tp = fp = fn = tn = exact = 0
    for url, expected_reasons in cases:
        actual_reasons = {signal.name for signal in analyze_url(url)}
        expected_risky = bool(expected_reasons)
        actual_risky = bool(actual_reasons)
        tp += expected_risky and actual_risky
        fp += not expected_risky and actual_risky
        fn += expected_risky and not actual_risky
        tn += not expected_risky and not actual_risky
        exact += actual_reasons == expected_reasons
    return {
        "support": len(cases),
        "risky_support": sum(bool(reasons) for _, reasons in cases),
        "safe_support": sum(not reasons for _, reasons in cases),
        "precision": _ratio(tp, tp + fp),
        "recall": _ratio(tp, tp + fn),
        "f1": _f1(tp, fp, fn),
        "balanced_accuracy": round((_ratio(tp, tp + fn) + _ratio(tn, tn + fp)) / 2, 8),
        "false_positive_rate": _ratio(fp, fp + tn),
        "exact_reason_accuracy": _ratio(exact, len(cases)),
    }


def benchmark_graph() -> dict[str, object]:
    secret = "synthetic-benchmark-secret"
    links: list[EntityLink] = []
    expected_edges: set[tuple[str, str]] = set()
    for index in range(20):
        value = (
            "https://cluster-a.example.test/path"
            if index < 5
            else "https://cluster-b.example.test/path"
            if index < 10
            else f"https://unique-{index}.example.test/path"
        )
        entity_id = stable_entity_id("url", value, secret)
        case_id = f"case-{index:02d}"
        links.append(
            EntityLink(
                case_id=case_id,
                created_at=datetime(2026, 1, index + 1, tzinfo=timezone.utc).isoformat(),
                predicted_label=LABELS[index % len(LABELS)],
                risk_level="medium",
                risk_score=55.0,
                entity_type="url",
                entity_id=entity_id,
                masked_value=mask_entity("url", value),
            )
        )
        if index < 10:
            expected_edges.add((f"case:{case_id}", f"entity:url:{entity_id}"))
    result = build_entity_graph(links, minimum_case_count=2)
    actual_edges = {(edge.source, edge.target) for edge in result.edges}
    tp = len(actual_edges & expected_edges)
    fp = len(actual_edges - expected_edges)
    fn = len(expected_edges - actual_edges)
    serialized = json.dumps(asdict(result), sort_keys=True)
    return {
        "support": len(links),
        "expected_edge_support": len(expected_edges),
        "edge_precision": _ratio(tp, tp + fp),
        "edge_recall": _ratio(tp, tp + fn),
        "edge_f1": _f1(tp, fp, fn),
        "component_exact_match": float(result.summary.component_count == 2),
        "privacy_leak_count": sum(
            value in serialized
            for value in (
                "cluster-a.example.test/path",
                "cluster-b.example.test/path",
                "synthetic-benchmark-secret",
            )
        ),
    }


def benchmark_ocr(
    *,
    engine: object | None = None,
    image_encoder: Callable[[str, str], bytes] | None = None,
    predictor: object | None = None,
) -> dict[str, object]:
    service = engine if engine is not None and hasattr(engine, "extract") else OcrService(engine=engine)
    encoder = image_encoder or _encode_text_image
    runtime = predictor or ModelPredictor()
    cases = _ocr_cases()
    total_chars = char_errors = total_words = word_errors = failures = 0
    label_matches = 0
    entity_tp = entity_fp = entity_fn = 0
    strata = {name: {"support": 0, "failures": 0, "char_errors": 0, "chars": 0} for name in ("clean", "low_contrast", "mild_blur")}
    observed_engine = getattr(engine, "engine_name", "tesseract")
    observed_languages = getattr(engine, "languages", "eng+hin")
    for reference, stratum in cases:
        strata[stratum]["support"] += 1
        image_bytes = encoder(reference, stratum)
        try:
            result = service.extract(image_bytes, "image/png")
            observed_engine = result.engine
            observed_languages = result.languages
            recognized = _canonical_ocr(result.text)
        except Exception:
            failures += 1
            strata[stratum]["failures"] += 1
            recognized = ""
        expected = _canonical_ocr(reference)
        character_distance = _edit_distance(expected, recognized)
        word_distance = _edit_distance(expected.split(), recognized.split())
        total_chars += len(expected)
        total_words += len(expected.split())
        char_errors += character_distance
        word_errors += word_distance
        strata[stratum]["char_errors"] += character_distance
        strata[stratum]["chars"] += len(expected)
        label_matches += runtime.predict(expected).label == runtime.predict(recognized).label
        expected_entities = {(item.type, item.value) for item in extract_entities(expected)}
        actual_entities = {(item.type, item.value) for item in extract_entities(recognized)}
        entity_tp += len(expected_entities & actual_entities)
        entity_fp += len(actual_entities - expected_entities)
        entity_fn += len(expected_entities - actual_entities)
    return {
        "support": len(cases),
        "engine": observed_engine,
        "languages": observed_languages,
        "character_error_rate": _ratio(char_errors, total_chars),
        "word_error_rate": _ratio(word_errors, total_words),
        "failure_rate": _ratio(failures, len(cases)),
        "downstream_label_agreement": _ratio(label_matches, len(cases)),
        "downstream_entity_f1": _f1(entity_tp, entity_fp, entity_fn),
        "by_stratum": {
            name: {
                "support": values["support"],
                "failure_rate": _ratio(values["failures"], values["support"]),
                "character_error_rate": _ratio(values["char_errors"], values["chars"]),
            }
            for name, values in strata.items()
        },
    }


def benchmark_complaint_drafts() -> dict[str, object]:
    cases = [
        (label, f"Synthetic {label} evidence at https://case.example.test/{index}")
        for label in LABELS
        for index in range(3)
    ]
    complete = evidence = consistent = editability = 0
    unsupported_identifiers = secret_leaks = 0
    identifier_pattern = re.compile(r"(?:https?://\S+|[\w.-]+@[\w.-]+|\b[6-9]\d{9}\b)")
    for label, text in cases:
        entities = extract_entities(text)
        draft = build_complaint_draft(label, "high", entities, text)
        complete += all(
            heading in draft
            for heading in (
                "Suspected fraud type:",
                "Risk level:",
                "Incident summary:",
                "Original message:",
                "Recommended manual action:",
            )
        )
        evidence += text in draft
        consistent += f"Suspected fraud type: {label}" in draft
        editability += draft.count("\n") >= 4 and len(draft) < 2_000
        allowed = set(identifier_pattern.findall(text))
        unsupported_identifiers += len(set(identifier_pattern.findall(draft)) - allowed)
        secret_leaks += any(marker in draft for marker in ("synthetic-benchmark-secret", "hmac_secret", "api_key"))
    support = len(cases)
    return {
        "support": support,
        "human_rated": False,
        "field_completeness": _ratio(complete, support),
        "expected_evidence_inclusion": _ratio(evidence, support),
        "category_consistency": _ratio(consistent, support),
        "unsupported_identifier_rate": _ratio(unsupported_identifiers, support),
        "secret_leak_count": secret_leaks,
        "editability_template_pass_rate": _ratio(editability, support),
        "interpretation": "Deterministic template checks; not a human judgement of complaint quality.",
    }


def run_subsystem_evaluation(
    output_dir: Path | str,
    *,
    ocr_engine: object | None = None,
    image_encoder: Callable[[str, str], bytes] | None = None,
) -> dict[str, object]:
    results = {
        "entity_extraction": benchmark_entities(),
        "url_risk": benchmark_urls(),
        "entity_graph": benchmark_graph(),
        "ocr": benchmark_ocr(engine=ocr_engine, image_encoder=image_encoder),
        "complaint_draft": benchmark_complaint_drafts(),
    }
    document: dict[str, object] = {
        "schema_version": 1,
        "fixture_policy": {
            "synthetic_only": True,
            "raw_fixture_text_committed": False,
            "row_level_predictions_committed": False,
            "interpretation": "Fixtures are generated from reviewed templates; only aggregates are emitted.",
        },
        "subsystems": results,
        "claim_boundary": (
            "These controlled synthetic subsystem checks complement, but do not replace, field or user studies."
        ),
    }
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    (output / "subsystem_summary.json").write_text(
        json.dumps(document, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    _write_subsystem_csv(results, output / "subsystem_metrics.csv")
    return document


def _write_subsystem_csv(results: Mapping[str, Mapping[str, object]], path: Path) -> None:
    rows = [
        ("entity_extraction", "micro_f1"),
        ("url_risk", "f1"),
        ("entity_graph", "edge_f1"),
        ("ocr", "downstream_label_agreement"),
        ("complaint_draft", "field_completeness"),
    ]
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(
            stream, fieldnames=("subsystem", "primary_metric", "value", "support"), lineterminator="\n"
        )
        writer.writeheader()
        for subsystem, metric in rows:
            writer.writerow(
                {
                    "subsystem": subsystem,
                    "primary_metric": metric,
                    "value": results[subsystem][metric],
                    "support": results[subsystem]["support"],
                }
            )


def _ocr_cases() -> list[tuple[str, str]]:
    messages = (
        "Urgent KYC verify now at https://kyc.example.test",
        "Share OTP code 4821 to verify account",
        "Courier parcel blocked pay Rs 850 today",
        "Guaranteed investment profit call 9876501234",
        "Aapka account abhi block hoga KYC update karein",
        "Refund collect request demo@upi PIN mat share karein",
        "Digital arrest warrant do not disconnect",
        "Work from home joining fee Rs 500",
    )
    return [(message, stratum) for stratum in ("clean", "low_contrast", "mild_blur") for message in messages]


def _encode_text_image(text: str, stratum: str) -> bytes:
    background = 255 if stratum != "low_contrast" else 220
    foreground = 0 if stratum != "low_contrast" else 135
    image = Image.new("L", (1_400, 160), color=background)
    draw = ImageDraw.Draw(image)
    draw.text((30, 55), text, fill=foreground)
    if stratum == "mild_blur":
        image = image.filter(ImageFilter.GaussianBlur(radius=0.6))
    stream = io.BytesIO()
    image.save(stream, format="PNG")
    return stream.getvalue()


def _canonical_ocr(text: str) -> str:
    return " ".join(text.casefold().split())


def _edit_distance(left: Sequence[object], right: Sequence[object]) -> int:
    previous = list(range(len(right) + 1))
    for left_index, left_value in enumerate(left, start=1):
        current = [left_index]
        for right_index, right_value in enumerate(right, start=1):
            current.append(
                min(
                    current[-1] + 1,
                    previous[right_index] + 1,
                    previous[right_index - 1] + (left_value != right_value),
                )
            )
        previous = current
    return previous[-1]


def _ratio(numerator: int, denominator: int) -> float:
    return round(numerator / denominator, 8) if denominator else 0.0


def _f1(true_positive: int, false_positive: int, false_negative: int) -> float:
    return _ratio(2 * true_positive, 2 * true_positive + false_positive + false_negative)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    arguments = parser.parse_args()
    run_subsystem_evaluation(arguments.output)


if __name__ == "__main__":
    main()
