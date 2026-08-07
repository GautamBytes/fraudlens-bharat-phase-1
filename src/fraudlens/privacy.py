"""Privacy-preserving entity helpers for persisted case relationships."""

import hashlib
import hmac
import re
from typing import Callable, Dict
from urllib.parse import urlsplit, urlunsplit


_SUPPORTED_ENTITY_TYPES = {"phone", "upi_id", "email", "url"}


def _required(entity_type: str, value: str) -> tuple[str, str]:
    normalized_type = entity_type.strip().casefold() if isinstance(entity_type, str) else ""
    if normalized_type not in _SUPPORTED_ENTITY_TYPES:
        raise ValueError("Unsupported entity type")
    if not isinstance(value, str) or not value.strip():
        raise ValueError("Entity value must not be empty")
    return normalized_type, value.strip()


def _normalize_phone(value: str) -> str:
    digits = re.sub(r"\D", "", value)
    if digits.startswith("91") and len(digits) == 12:
        digits = digits[2:]
    if re.fullmatch(r"[6-9]\d{9}", digits) is None:
        raise ValueError("Phone entity must be a valid Indian subscriber number")
    return digits


def _normalize_url(value: str) -> str:
    parsed = urlsplit(value)
    if not parsed.scheme or not parsed.netloc:
        raise ValueError("URL entity must include a scheme and host")
    if parsed.scheme.casefold() not in {"http", "https"} or not parsed.hostname:
        raise ValueError("URL entity must include a valid HTTP host")
    hostname = parsed.hostname.casefold()
    netloc = hostname
    if parsed.port is not None:
        netloc = "{}:{}".format(hostname, parsed.port)
    return urlunsplit((parsed.scheme.casefold(), netloc, parsed.path or "", parsed.query, ""))


def normalize_entity_value(entity_type: str, value: str) -> str:
    """Return a stable canonical value suitable only for deriving an HMAC."""

    normalized_type, raw_value = _required(entity_type, value)
    if normalized_type == "phone":
        return _normalize_phone(raw_value)
    if normalized_type in {"upi_id", "email"}:
        return raw_value.casefold()
    return _normalize_url(raw_value)


def stable_entity_id(entity_type: str, value: str, secret: str) -> str:
    """Derive an opaque, namespaced stable identifier without storing raw PII."""

    if not isinstance(secret, str) or not secret:
        raise ValueError("HMAC secret must not be empty")
    normalized_type, _ = _required(entity_type, value)
    canonical_value = normalize_entity_value(normalized_type, value)
    payload = "{}:{}".format(normalized_type, canonical_value).encode("utf-8")
    digest = hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()
    return "{}_{}".format(normalized_type, digest)


def _mask_phone(value: str) -> str:
    return "*" * max(0, len(value) - 4) + value[-4:]


def _mask_local(value: str) -> str:
    return value[:1] + "***"


def _mask_upi(value: str) -> str:
    local, provider = value.split("@", 1)
    return "{}@{}".format(_mask_local(local), provider)


def _mask_email(value: str) -> str:
    local, domain = value.rsplit("@", 1)
    return "{}@{}".format(_mask_local(local), domain)


def _mask_url(value: str) -> str:
    return urlsplit(value).hostname or ""


_MASKERS: Dict[str, Callable[[str], str]] = {
    "phone": _mask_phone,
    "upi_id": _mask_upi,
    "email": _mask_email,
    "url": _mask_url,
}


def mask_entity(entity_type: str, value: str) -> str:
    """Return a useful, non-raw display representation for a supported entity."""

    normalized_type = entity_type.strip().casefold() if isinstance(entity_type, str) else ""
    canonical_value = normalize_entity_value(normalized_type, value)
    return _MASKERS[normalized_type](canonical_value)
