from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_installation_docs_separate_runtime_and_contributor_dependencies():
    for relative_path in ("README.md", "docs/installation_guide.md"):
        documentation = (ROOT / relative_path).read_text(encoding="utf-8")

        assert "Runtime installation" in documentation
        assert "Contributor and test installation" in documentation
        assert "pip install -r requirements.txt" in documentation
        assert "pip install -r requirements-dev.txt" in documentation


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

    for version in ('"3.10"', '"3.11"', '"3.12"'):
        assert version in workflow
    assert '"3.9"' not in workflow
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
    assert "if: matrix.python-version == '3.11'" in artifact_gate_body
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
