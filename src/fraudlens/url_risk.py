import ipaddress
from typing import List
from urllib.parse import urlparse

from fraudlens.config import SHORTENER_DOMAINS, SUSPICIOUS_URL_KEYWORDS
from fraudlens.schemas import RiskSignal


def _parse_url(raw_url: str):
    candidate = raw_url.strip()
    if candidate.startswith("www."):
        candidate = "http://" + candidate
    return urlparse(candidate)


def _hostname(parsed) -> str:
    return (parsed.hostname or "").lower()


def _is_ip_hostname(hostname: str) -> bool:
    try:
        ipaddress.ip_address(hostname)
        return True
    except ValueError:
        return False


def analyze_url(raw_url: str) -> List[RiskSignal]:
    parsed = _parse_url(raw_url)
    host = _hostname(parsed)
    url_lower = raw_url.lower()
    signals: List[RiskSignal] = []

    if parsed.scheme != "https":
        signals.append(
            RiskSignal(
                name="non_https_url",
                score=15,
                reason="URL does not use HTTPS",
                evidence=raw_url,
            )
        )

    if host in SHORTENER_DOMAINS:
        signals.append(
            RiskSignal(
                name="shortened_url",
                score=25,
                reason="Shortened URLs hide the final destination",
                evidence=raw_url,
            )
        )

    if host and _is_ip_hostname(host):
        signals.append(
            RiskSignal(
                name="ip_address_url",
                score=25,
                reason="URL uses a raw IP address instead of a normal domain",
                evidence=raw_url,
            )
        )

    for keyword in sorted(SUSPICIOUS_URL_KEYWORDS):
        if keyword in url_lower:
            signals.append(
                RiskSignal(
                    name="suspicious_url_keyword",
                    score=10,
                    reason=f"URL contains suspicious keyword '{keyword}'",
                    evidence=raw_url,
                )
            )

    if host.count("-") >= 2:
        signals.append(
            RiskSignal(
                name="hyphenated_domain",
                score=8,
                reason="Domain contains multiple hyphens, a common phishing pattern",
                evidence=raw_url,
            )
        )

    return signals


def analyze_urls(urls: list[str]) -> List[RiskSignal]:
    signals: List[RiskSignal] = []
    for url in urls:
        signals.extend(analyze_url(url))
    return signals

