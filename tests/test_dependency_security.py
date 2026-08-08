from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_installation_docs_separate_runtime_and_contributor_dependencies():
    for relative_path in ("README.md", "docs/installation_guide.md"):
        documentation = (ROOT / relative_path).read_text(encoding="utf-8")

        assert "Runtime installation" in documentation
        assert "Contributor and test installation" in documentation
        assert "pip install -r requirements.txt" in documentation
        assert "pip install -r requirements-dev.txt" in documentation


def test_ocr_runtime_dependencies_are_documented_for_supported_platforms():
    for relative_path in ("README.md", "docs/installation_guide.md"):
        documentation = (ROOT / relative_path).read_text(encoding="utf-8")

        assert "brew install tesseract tesseract-lang" in documentation
        assert (
            "tesseract-ocr tesseract-ocr-eng tesseract-ocr-hin"
            in documentation
        )


def test_screenshot_contract_is_documented_for_api_and_dashboard_users():
    documentation = " ".join("\n".join(
        (ROOT / relative_path).read_text(encoding="utf-8")
        for relative_path in ("README.md", "docs/user_manual.md")
    ).split())

    for expected_text in (
        "POST /analyze-image",
        "Content-Type: image/png",
        "--data-binary @screenshot.png",
        "PNG and JPEG",
        "5 MiB",
        "4096 x 4096",
        "16,000,000 pixels",
        "English and Hindi",
        "Images are never retained",
        "OCR text is stored only when you explicitly enable local case storage",
    ):
        assert expected_text in documentation


def test_screenshot_api_error_contract_is_documented():
    documentation = (ROOT / "docs/user_manual.md").read_text(encoding="utf-8")

    for status_code in ("400", "413", "415", "422", "503", "504", "500"):
        assert f"`{status_code}`" in documentation
    assert "generic error messages" in documentation


def test_screenshot_test_inventory_covers_security_boundaries():
    documentation = (ROOT / "docs/test_cases.md").read_text(encoding="utf-8")

    for test_case in (
        "Screenshot OCR analysis",
        "Screenshot format rejection",
        "Screenshot size rejection",
        "Screenshot dimension and pixel rejection",
        "Screenshot retention consent",
        "OCR failure redaction",
    ):
        assert test_case in documentation


def test_entity_graph_privacy_and_operational_contract_is_documented():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    manual = (ROOT / "docs/user_manual.md").read_text(encoding="utf-8")
    inventory = (ROOT / "docs/test_cases.md").read_text(encoding="utf-8")
    documentation = " ".join((readme + manual).split())

    for expected_text in (
        "explicitly stored, unexpired cases",
        "phone numbers, UPI IDs, email addresses, and URLs",
        "masked labels",
        "API entity nodes expose opaque HMAC-backed identifiers",
        "dashboard shows masked labels and hides opaque identifiers",
        "does not include raw text or raw entity values",
        "GET /graph",
        "minimum_case_count=2",
        "case_limit=100",
        "fixed internal max_edges=1000",
        "minimum_case_count must be between 2 and 20",
        "case_limit must be between 1 and 100",
        "does not run the graph query until explicit Refresh",
        "no qualifying stored cases",
        "truncated",
        "Deleting a case, clearing case history, or retention expiry removes its graph links",
        "does not change a case's risk score or fraud classification",
        "does not perform fraud-network detection",
        "GNN",
    ):
        assert expected_text in documentation

    for test_case in (
        "Entity graph privacy contract",
        "Entity graph retention and deletion",
        "Entity graph API bounds and empty result",
        "Entity graph dashboard refresh and truncation",
    ):
        assert test_case in inventory


def test_historical_and_living_docs_contextualize_current_ocr_and_graph_scope():
    historical_paths = (
        "docs/phase1_report.md",
        "docs/presentation/presentation_script.md",
    )
    for relative_path in historical_paths:
        documentation = (ROOT / relative_path).read_text(encoding="utf-8")
        documentation = " ".join(
            documentation.replace("\n> ", "\n").replace("`", "").split()
        )
        assert "Current-scope note (2026-08-08)" in documentation
        assert "preserves a Phase 1 snapshot" in documentation
        assert "OCR and basic privacy-safe graph analytics now exist" in documentation
        assert "Transformer fine-tuning and GNNs remain out of scope" in documentation
        assert "README.md is the current status source" in documentation

    comparative = (ROOT / "docs/comparative_analysis.md").read_text(encoding="utf-8")
    literature = (ROOT / "docs/literature_review.md").read_text(encoding="utf-8")
    evaluation = (ROOT / "docs/evaluation_plan.md").read_text(encoding="utf-8")
    living_documentation = " ".join((comparative + literature + evaluation).split())

    assert "current implementation includes screenshot OCR" in living_documentation
    assert "basic privacy-safe graph analytics" in living_documentation
    assert "explicitly stored, unexpired cases" in living_documentation
    assert "does not perform production fraud-network detection or use a GNN" in living_documentation
    assert "Transformer comparison and GNN research remain future work" in living_documentation
    assert (
        "Phase 1 only extracts identifiers from one message at a time. "
        "It does not yet model relationships across cases."
        not in comparative
    )
    assert "FraudLens Bharat does not implement graph analytics in Phase 1." not in literature


def test_dependency_and_ci_security_baseline():
    requirements = (ROOT / "requirements.txt").read_text(encoding="utf-8")
    development_requirements = (ROOT / "requirements-dev.txt").read_text(
        encoding="utf-8"
    )
    workflow = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
    setup = (ROOT / "setup.py").read_text(encoding="utf-8")
    lock = (ROOT / "requirements.lock").read_text(encoding="utf-8")

    for dependency in (
        "fastapi==0.141.1",
        "streamlit==1.54.0",
        "python-multipart==0.0.31",
        "Pillow==12.3.0",
    ):
        assert dependency in requirements
    for dependency in ("pip==26.1.2", "pytest==9.0.3", "setuptools==83.0.0"):
        assert dependency in development_requirements
    assert "-r requirements.txt" in development_requirements
    assert "--hash=sha256:" in lock
    assert "greenlet==" in lock
    assert 'python_requires=">=3.10"' in setup

    for version in ('"3.10"', '"3.11.15"', '"3.12"'):
        assert version in workflow
    assert '"3.9"' not in workflow
    assert '"3.11"' not in workflow
    assert "permissions:\n  contents: read" in workflow
    assert "actions/checkout@11d5960a326750d5838078e36cf38b85af677262" in workflow
    assert "actions/setup-python@a26af69be951a213d495a4c3e4e4022e16d87065" in workflow
    assert "persist-credentials: false" in workflow
    assert "--require-hashes -r requirements.lock" in workflow
    assert "--no-index --no-deps -r requirements-dev.txt" in workflow
    assert "-e . --no-deps" in workflow

    artifact_gate = workflow.index("- name: Verify reproducible release artifacts")
    test_step = workflow.index("- name: Run tests")
    assert artifact_gate < test_step
    artifact_gate_body = workflow[artifact_gate:test_step]
    assert "if: matrix.python-version == '3.11.15'" in artifact_gate_body
    assert "train_baseline(artifact_dir=Path(" in artifact_gate_body
    for artifact in (
        "baseline_classifier.joblib",
        "vectorizer.joblib",
        "label_encoder.joblib",
        "metrics.json",
        "model_metadata.json",
        "artifact_manifest.json",
    ):
        assert artifact in artifact_gate_body
