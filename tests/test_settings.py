from pathlib import Path

import pytest

from fraudlens.config import DB_PATH
from fraudlens.settings import from_env


def test_from_env_uses_secure_development_defaults(monkeypatch):
    for name in (
        "FRAUDLENS_MODEL_BACKEND",
        "FRAUDLENS_DB_PATH",
        "FRAUDLENS_HMAC_SECRET",
        "FRAUDLENS_RETENTION_DAYS",
        "FRAUDLENS_STORE_CASES",
        "FRAUDLENS_ENVIRONMENT",
        "FRAUDLENS_ALLOWED_HOSTS",
    ):
        monkeypatch.delenv(name, raising=False)

    settings = from_env()

    assert settings.model_backend == "tfidf"
    assert settings.database_path == DB_PATH
    assert settings.hmac_secret
    assert settings.retention_days == 30
    assert settings.store_cases_by_default is False
    assert settings.environment == "development"
    assert settings.allowed_hosts == ()


def test_from_env_parses_explicit_runtime_values(monkeypatch, tmp_path):
    monkeypatch.setenv("FRAUDLENS_MODEL_BACKEND", "muril")
    monkeypatch.setenv("FRAUDLENS_DB_PATH", str(tmp_path / "cases.sqlite3"))
    monkeypatch.setenv("FRAUDLENS_HMAC_SECRET", "a-secure-local-testing-secret-with-32-bytes")
    monkeypatch.setenv("FRAUDLENS_RETENTION_DAYS", "90")
    monkeypatch.setenv("FRAUDLENS_STORE_CASES", "true")
    monkeypatch.setenv("FRAUDLENS_ENVIRONMENT", "staging")
    monkeypatch.setenv("FRAUDLENS_ALLOWED_HOSTS", "api.example.in, localhost ,")

    settings = from_env()

    assert settings.model_backend == "muril"
    assert settings.database_path == Path(tmp_path / "cases.sqlite3")
    assert settings.retention_days == 90
    assert settings.store_cases_by_default is True
    assert settings.environment == "staging"
    assert settings.allowed_hosts == ("api.example.in", "localhost")


@pytest.mark.parametrize(
    ("name", "value"),
    [
        ("FRAUDLENS_MODEL_BACKEND", "remote"),
        ("FRAUDLENS_RETENTION_DAYS", "0"),
        ("FRAUDLENS_RETENTION_DAYS", "not-a-number"),
        ("FRAUDLENS_STORE_CASES", "sometimes"),
    ],
)
def test_from_env_rejects_invalid_runtime_values(monkeypatch, name, value):
    monkeypatch.setenv(name, value)

    with pytest.raises(ValueError):
        from_env()


@pytest.mark.parametrize("secret", [None, "too-short"])
def test_from_env_requires_a_strong_hmac_secret_in_production(monkeypatch, secret):
    monkeypatch.setenv("FRAUDLENS_ENVIRONMENT", "production")
    if secret is None:
        monkeypatch.delenv("FRAUDLENS_HMAC_SECRET", raising=False)
    else:
        monkeypatch.setenv("FRAUDLENS_HMAC_SECRET", secret)

    with pytest.raises(ValueError):
        from_env()
