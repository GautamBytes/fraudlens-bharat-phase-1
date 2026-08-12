import csv
import json

from fraudlens.ocr import OcrResult
from fraudlens.subsystem_evaluation import (
    benchmark_complaint_drafts,
    benchmark_entities,
    benchmark_graph,
    benchmark_ocr,
    benchmark_urls,
    run_subsystem_evaluation,
)


class _PerfectOcr:
    engine_name = "fixture-ocr"
    languages = "eng+hin"

    def extract(self, image_bytes: bytes, media_type: str) -> OcrResult:
        del media_type
        text = image_bytes.decode("utf-8")
        return OcrResult(text=text, engine=self.engine_name, languages=self.languages, width=800, height=140)


def test_subsystem_fixtures_have_declared_minimum_support_and_real_metrics():
    entities = benchmark_entities()
    urls = benchmark_urls()
    graph = benchmark_graph()
    complaints = benchmark_complaint_drafts()

    assert entities["support"] >= 40
    assert entities["micro_f1"] >= 0
    assert set(entities["per_type"]) >= {
        "phone",
        "upi_id",
        "email",
        "url",
        "money",
        "otp_like_code",
        "urgency_phrase",
        "threat_phrase",
    }
    assert urls["support"] >= 40
    assert set(urls) >= {
        "precision",
        "recall",
        "f1",
        "balanced_accuracy",
        "false_positive_rate",
        "exact_reason_accuracy",
    }
    assert graph["support"] >= 20
    assert set(graph) >= {
        "edge_precision",
        "edge_recall",
        "edge_f1",
        "component_exact_match",
        "privacy_leak_count",
    }
    assert complaints["support"] >= 24
    assert complaints["human_rated"] is False
    assert set(complaints) >= {
        "field_completeness",
        "expected_evidence_inclusion",
        "category_consistency",
        "unsupported_identifier_rate",
        "secret_leak_count",
        "editability_template_pass_rate",
    }


def test_ocr_benchmark_reports_quality_and_downstream_metrics_with_injected_engine():
    result = benchmark_ocr(engine=_PerfectOcr(), image_encoder=lambda text, _: text.encode("utf-8"))

    assert result["support"] >= 24
    assert result["character_error_rate"] == 0
    assert result["word_error_rate"] == 0
    assert result["failure_rate"] == 0
    assert result["engine"] == "fixture-ocr"
    assert result["languages"] == "eng+hin"
    assert set(result["by_stratum"]) == {"clean", "low_contrast", "mild_blur"}


def test_subsystem_outputs_are_deterministic_and_aggregate_only(tmp_path):
    first = tmp_path / "first"
    second = tmp_path / "second"
    report = run_subsystem_evaluation(first, ocr_engine=_PerfectOcr(), image_encoder=lambda text, _: text.encode("utf-8"))
    run_subsystem_evaluation(second, ocr_engine=_PerfectOcr(), image_encoder=lambda text, _: text.encode("utf-8"))

    assert (first / "subsystem_summary.json").read_bytes() == (
        second / "subsystem_summary.json"
    ).read_bytes()
    assert (first / "subsystem_metrics.csv").read_bytes() == (
        second / "subsystem_metrics.csv"
    ).read_bytes()
    payload = json.loads((first / "subsystem_summary.json").read_text(encoding="utf-8"))
    assert payload == report
    assert payload["fixture_policy"]["synthetic_only"] is True
    assert payload["fixture_policy"]["raw_fixture_text_committed"] is False
    assert "9876543210" not in json.dumps(payload)
    with (first / "subsystem_metrics.csv").open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))
    assert {row["subsystem"] for row in rows} == {
        "entity_extraction",
        "url_risk",
        "entity_graph",
        "ocr",
        "complaint_draft",
    }
