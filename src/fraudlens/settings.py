import os
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Optional, Tuple

from fraudlens.config import DB_PATH


_DEFAULT_ENVIRONMENT = "development"
_LOCAL_DEMO_HMAC_SECRET = "local-demo-only-secret-not-for-production"
_VALID_MODEL_BACKENDS = {"tfidf", "muril"}
_MIN_PRODUCTION_HMAC_SECRET_LENGTH = 32


@dataclass(frozen=True)
class Settings:
    model_backend: str
    database_path: Path
    hmac_secret: str
    retention_days: int
    store_cases_by_default: bool
    environment: str
    allowed_hosts: Tuple[str, ...]

    @classmethod
    def from_env(cls, environ: Optional[Mapping[str, str]] = None) -> "Settings":
        values = os.environ if environ is None else environ
        environment = values.get("FRAUDLENS_ENVIRONMENT", _DEFAULT_ENVIRONMENT).strip().lower()
        model_backend = values.get("FRAUDLENS_MODEL_BACKEND", "tfidf").strip().lower()
        if model_backend not in _VALID_MODEL_BACKENDS:
            raise ValueError("FRAUDLENS_MODEL_BACKEND must be one of: tfidf, muril")

        database_path = Path(values.get("FRAUDLENS_DB_PATH", str(DB_PATH))).expanduser()
        retention_days = _parse_positive_int(values.get("FRAUDLENS_RETENTION_DAYS", "30"), "FRAUDLENS_RETENTION_DAYS")
        store_cases_by_default = _parse_bool(
            values.get("FRAUDLENS_STORE_CASES", "false"), "FRAUDLENS_STORE_CASES"
        )
        allowed_hosts = tuple(
            host for host in (item.strip() for item in values.get("FRAUDLENS_ALLOWED_HOSTS", "").split(",")) if host
        )

        configured_secret = values.get("FRAUDLENS_HMAC_SECRET")
        if environment == "production":
            if not _is_strong_production_secret(configured_secret):
                raise ValueError(
                    "FRAUDLENS_HMAC_SECRET must be set to a non-default secret of at least 32 characters in production"
                )
            hmac_secret = configured_secret
        else:
            hmac_secret = configured_secret or _LOCAL_DEMO_HMAC_SECRET

        return cls(
            model_backend=model_backend,
            database_path=database_path,
            hmac_secret=hmac_secret,
            retention_days=retention_days,
            store_cases_by_default=store_cases_by_default,
            environment=environment,
            allowed_hosts=allowed_hosts,
        )


def from_env(environ: Optional[Mapping[str, str]] = None) -> Settings:
    return Settings.from_env(environ)


def _parse_positive_int(value: str, name: str) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        raise ValueError(f"{name} must be a positive integer") from None
    if parsed <= 0:
        raise ValueError(f"{name} must be a positive integer")
    return parsed


def _parse_bool(value: str, name: str) -> bool:
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    raise ValueError(f"{name} must be a boolean")


def _is_strong_production_secret(secret: Optional[str]) -> bool:
    if not secret or len(secret) < _MIN_PRODUCTION_HMAC_SECRET_LENGTH:
        return False
    if secret == _LOCAL_DEMO_HMAC_SECRET:
        return False
    return len(set(secret)) > 1
