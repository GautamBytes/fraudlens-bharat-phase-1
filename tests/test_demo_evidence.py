import inspect
import json
from dataclasses import asdict
from pathlib import Path

from PIL import Image

from fraudlens.analysis_service import AnalysisInput, create_analysis_service
from fraudlens import dashboard, generate_demo_cases
from fraudlens.analysis_service import DatabaseCaseStore
from fraudlens.settings import Settings


ROOT = Path(__file__).resolve().parents[1]


def test_release_model_classifies_every_named_demo_as_advertised():
    service = create_analysis_service(Settings.from_env())
    expected_labels = {
        "Fake KYC SMS": "kyc_scam",
        "OTP Phishing": "otp_phishing",
        "Fake Job Scam": "fake_job",
        "Investment Scam": "investment_scam",
    }

    for name, text in dashboard.DEMO_MESSAGES.items():
        result = service.analyze(AnalysisInput(text=text, store_case=False))

        assert result.predicted_label == expected_labels[name], name
        assert result.metadata["prediction_abstained"] is False


def test_dashboard_identifies_the_final_phase_1_and_phase_2_scope():
    source = inspect.getsource(dashboard.main)

    assert "Final Phase 1 + Phase 2 Hinglish cyber-fraud triage prototype" in source
    assert "Phase 1 baseline prototype" not in source


def test_dashboard_and_generated_demo_catalogs_cannot_drift():
    expected_slug_by_button = {
        "Fake KYC SMS": "fake_kyc_sms",
        "OTP Phishing": "otp_phishing",
        "Fake Job Scam": "fake_job_scam",
        "Investment Scam": "investment_scam",
    }

    assert {
        button: generate_demo_cases.DEMO_CASES[slug]
        for button, slug in expected_slug_by_button.items()
    } == dashboard.DEMO_MESSAGES


def test_generated_demo_outputs_are_byte_deterministic(tmp_path, monkeypatch):
    first = tmp_path / "first"
    second = tmp_path / "second"

    monkeypatch.setattr(generate_demo_cases, "DEMO_CASES_DIR", first)
    generate_demo_cases.main()
    monkeypatch.setattr(generate_demo_cases, "DEMO_CASES_DIR", second)
    generate_demo_cases.main()

    first_files = {path.name: path.read_bytes() for path in first.glob("*.json")}
    second_files = {path.name: path.read_bytes() for path in second.glob("*.json")}
    assert first_files == second_files
    assert set(first_files) == {
        "fake_kyc_sms.json",
        "otp_phishing.json",
        "fake_job_scam.json",
        "investment_scam.json",
    }
    for name, content in first_files.items():
        payload = json.loads(content)
        assert payload["case_id"] == "demo-{}".format(name.removesuffix(".json"))
        assert payload["created_at"] == "2026-08-10T12:00:00"
        assert payload["metadata"]["stored"] is False


def test_explicit_generator_matches_committed_demo_evidence(tmp_path):
    generator = getattr(generate_demo_cases, "generate_demo_cases", None)
    assert generator is not None

    written = generator(tmp_path)

    assert {path.name for path in written} == {
        "fake_kyc_sms.json",
        "otp_phishing.json",
        "fake_job_scam.json",
        "investment_scam.json",
    }
    for path in written:
        assert path.read_bytes() == (ROOT / "outputs" / "demo_cases" / path.name).read_bytes()


def test_ci_regenerates_and_compares_demo_evidence():
    workflow = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")

    assert "Verify deterministic demo evidence" in workflow
    assert "fraudlens.generate_demo_cases --output" in workflow
    assert 'cmp "$demo_tmp/$artifact" "outputs/demo_cases/$artifact"' in workflow


def test_graph_demo_preparation_creates_two_safely_linked_cases(tmp_path):
    prepare_graph = getattr(generate_demo_cases, "prepare_graph_demo_database", None)
    assert prepare_graph is not None
    database_path = tmp_path / "graph-demo.db"

    results = prepare_graph(database_path)
    graph = DatabaseCaseStore(database_path).entity_graph(
        minimum_case_count=2,
        case_limit=100,
        max_edges=1000,
    )

    assert [result.case_id for result in results] == ["graph-demo-1", "graph-demo-2"]
    assert all(result.metadata["stored"] is True for result in results)
    assert graph.summary.case_count == 2
    assert graph.summary.entity_count == 1
    assert graph.summary.edge_count == 2
    assert graph.entity_nodes[0].masked_value == "fraud-demo.example"
    assert "https://fraud-demo.example/claim" not in json.dumps(
        asdict(graph)
    )


def test_ocr_demo_screenshot_is_safe_valid_and_reproducible(tmp_path):
    generate_screenshot = getattr(generate_demo_cases, "generate_ocr_demo_screenshot", None)
    assert generate_screenshot is not None
    first = generate_screenshot(tmp_path / "first.png")
    second = generate_screenshot(tmp_path / "second.png")

    assert first.read_bytes() == second.read_bytes()
    with Image.open(first) as image:
        assert image.format == "PNG"
        assert image.mode == "RGB"
        assert image.size == (1200, 500)
        assert image.info == {}
    committed = ROOT / "data" / "demo" / "otp_phishing_screenshot.png"
    with Image.open(committed) as image:
        assert image.format == "PNG"
        assert image.mode == "RGB"
        assert image.size == (1200, 500)
        assert image.info == {}


def test_demo_cli_prepares_json_screenshot_and_graph_database(tmp_path):
    output_dir = tmp_path / "json"
    screenshot_path = tmp_path / "demo.png"
    database_path = tmp_path / "graph.db"

    generate_demo_cases.main(
        [
            "--output",
            str(output_dir),
            "--screenshot-output",
            str(screenshot_path),
            "--graph-database",
            str(database_path),
        ]
    )

    assert len(list(output_dir.glob("*.json"))) == 4
    assert screenshot_path.is_file()
    assert DatabaseCaseStore(database_path).entity_graph().summary.case_count == 2
