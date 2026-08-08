from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_docker_runtime_is_non_root_locked_and_has_ocr_languages():
    dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")

    assert dockerfile.startswith("# syntax=docker/dockerfile:1.7@sha256:")
    assert "python:3.11.15-slim-bookworm@sha256:" in dockerfile
    assert "pip install --only-binary=:all: --require-hashes -r requirements-runtime.lock" in dockerfile
    assert "tesseract-ocr-eng" in dockerfile
    assert "tesseract-ocr-hin" in dockerfile
    assert "USER 10001:10001" in dockerfile
    assert "HEALTHCHECK" in dockerfile
    assert "http://127.0.0.1:8000/ready" in dockerfile
    assert 'CMD ["uvicorn", "fraudlens.api:app"' in dockerfile
    assert "--no-access-log" in dockerfile
    assert "FRAUDLENS_HMAC_SECRET" not in dockerfile
    assert "--reload" not in dockerfile


def test_compose_enforces_production_boundaries_for_both_services():
    compose = (ROOT / "compose.yaml").read_text(encoding="utf-8")

    assert "FRAUDLENS_ENVIRONMENT: production" in compose
    assert "FRAUDLENS_HMAC_SECRET: ${FRAUDLENS_HMAC_SECRET:?" in compose
    assert "FRAUDLENS_STORE_CASES: \"false\"" in compose
    assert compose.count("read_only: true") == 2
    assert compose.count("no-new-privileges:true") == 2
    assert compose.count("cap_drop:") == 2
    assert "127.0.0.1:8000:8000" in compose
    assert "127.0.0.1:8501:8501" in compose
    assert "fraudlens-data:/data" in compose
    assert "_stcore/health" in compose


def test_build_context_excludes_local_and_sensitive_runtime_state():
    ignored = (ROOT / ".dockerignore").read_text(encoding="utf-8").splitlines()

    for required in (
        ".git",
        ".env",
        ".venv",
        "**/__pycache__",
        "*.sqlite3",
        "outputs",
        "tests",
    ):
        assert required in ignored


def test_example_environment_contains_no_secret_value():
    example = (ROOT / ".env.example").read_text(encoding="utf-8")
    values = dict(
        line.split("=", 1)
        for line in example.splitlines()
        if line and not line.startswith("#")
    )

    assert values["FRAUDLENS_HMAC_SECRET"] == ""
    assert values["FRAUDLENS_ALLOWED_HOSTS"] == "localhost,127.0.0.1"
