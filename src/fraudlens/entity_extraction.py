import re
from typing import Iterable, List

from fraudlens.config import THREAT_KEYWORDS, URGENCY_KEYWORDS
from fraudlens.schemas import Entity


URL_RE = re.compile(r"\b(?:https?://|www\.)[^\s<>'\"]+", re.IGNORECASE)
EMAIL_RE = re.compile(r"\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b")
UPI_RE = re.compile(r"\b[a-zA-Z0-9._-]{2,64}@[a-zA-Z]{2,32}\b")
PHONE_RE = re.compile(r"(?<!\d)(?:\+?91[\s-]?)?[6-9]\d{4}[\s-]?\d{5}(?!\d)")
MONEY_RE = re.compile(
    r"(?:rs\.?|inr|rupees?)\s*[:\-]?\s*(?:\d{1,7}|\d{1,3}(?:,\d{3})+)(?:\.\d{1,2})?|(?:\d{1,7}|\d{1,3}(?:,\d{3})+)(?:\.\d{1,2})?\s*(?:rs\.?|inr|rupees?)",
    re.IGNORECASE,
)
MONEY_CONTEXT_RE = re.compile(
    r"\b(?:pay|paid|send|deposit|invest|investment|fee|charge|refund|cashback|amount|salary|profit|loan|credit|return)"
    r"\b[^0-9]{0,25}((?:\d{1,7}|\d{1,3}(?:,\d{3})+)(?:\.\d{1,2})?)"
    r"|((?:\d{1,7}|\d{1,3}(?:,\d{3})+)(?:\.\d{1,2})?)\s*"
    r"(?:cashback|refund|fee|charge|salary|profit|loan|credit|return)",
    re.IGNORECASE,
)
OTP_CONTEXT_RE = re.compile(r"\b(?:otp|pin|code|verification code|cvv)\b[^0-9]{0,30}(\d{4,8})", re.IGNORECASE)


def _unique(values: Iterable[str]) -> list[str]:
    seen = set()
    result = []
    for value in values:
        normalized = value.strip().rstrip(".,;:)")
        if normalized and normalized not in seen:
            seen.add(normalized)
            result.append(normalized)
    return result


def _normalize_phone(phone: str) -> str:
    digits = re.sub(r"\D", "", phone)
    if digits.startswith("91") and len(digits) == 12:
        digits = digits[2:]
    return digits


def extract_entities(text: str) -> List[Entity]:
    entities: List[Entity] = []

    email_matches = list(EMAIL_RE.finditer(text))
    email_spans = [match.span() for match in email_matches]
    emails = _unique(match.group(0) for match in email_matches)
    urls = _unique(URL_RE.findall(text))
    upi_ids = _unique(
        match.group(0)
        for match in UPI_RE.finditer(text)
        if not any(match.start() >= start and match.end() <= end for start, end in email_spans)
    )
    phones = _unique(_normalize_phone(phone) for phone in PHONE_RE.findall(text))
    currency_money = MONEY_RE.findall(text)
    contextual_money = []
    for match in MONEY_CONTEXT_RE.finditer(text):
        amount = next(group for group in match.groups() if group)
        if not any(re.search(rf"(?<!\d){re.escape(amount)}(?!\d)", value) for value in currency_money):
            contextual_money.append(amount)
    money_amounts = _unique([*currency_money, *contextual_money])
    otp_codes = _unique(match.group(1) for match in OTP_CONTEXT_RE.finditer(text))

    for value in phones:
        entities.append(Entity(type="phone", value=value))
    for value in upi_ids:
        entities.append(Entity(type="upi_id", value=value))
    for value in urls:
        entities.append(Entity(type="url", value=value))
    for value in emails:
        entities.append(Entity(type="email", value=value))
    for value in money_amounts:
        entities.append(Entity(type="money", value=value))
    for value in otp_codes:
        entities.append(Entity(type="otp_like_code", value=value, confidence=0.85))

    lower_text = text.lower()
    for keyword in sorted(URGENCY_KEYWORDS):
        if keyword in lower_text:
            entities.append(Entity(type="urgency_phrase", value=keyword, confidence=0.8, source="keyword"))
    for keyword in sorted(THREAT_KEYWORDS):
        if keyword in lower_text:
            entities.append(Entity(type="threat_phrase", value=keyword, confidence=0.8, source="keyword"))

    return entities
