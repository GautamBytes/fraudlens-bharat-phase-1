import re
import unicodedata


CATEGORY_MARKERS = {
    "kyc_scam": (
        "kyc",
        "ekyc",
        "aadhaar",
        "pan",
        "account block",
        "wallet freeze",
        "re-verification",
    ),
    "digital_arrest": (
        "digital arrest",
        "arrest",
        "warrant",
        "cbi",
        "cyber cell",
        "court",
        "money laundering",
        "custody",
        "do not inform",
        "video",
        "officer",
        "close fir",
        "fir case",
        "case id",
        "settlement",
        "monitor",
        "do not disconnect",
        "line pe raho",
        "senior officer",
        "verification payment",
        "security amount",
    ),
    "fake_job": (
        "job",
        "salary",
        "registration fee",
        "joining",
        "hr",
        "work from home",
        "task",
        "offer letter",
        "selected",
        "interview",
        "ground staff",
        "typing work",
    ),
    "investment_scam": (
        "investment",
        "crypto",
        "trading",
        "double",
        "guaranteed",
        "profit",
        "vip",
        "stock",
        "2x return",
    ),
    "loan_scam": (
        "loan",
        "processing fee",
        "cibil",
        "disbursal",
        "recovery",
        "instant loan",
        "noc fee",
        "file charge",
        "insurance fee",
    ),
    "courier_scam": (
        "parcel no",
        "courier",
        "fedex",
        "dhl",
        "shipment",
        "delivery",
        "clearance",
        "drugs detected",
        "custom department",
        "sim card parcel",
        "parcel blocked",
    ),
    "upi_refund_scam": (
        "refund",
        "cashback",
        "collect request",
        "receive money",
        "upi pin",
        "qr",
        "mandate",
    ),
    "otp_phishing": (
        "otp",
        "password",
        "cvv",
        "pin",
        "verification code",
        "login attempt",
        "code share",
    ),
}

STRONG_CATEGORY_MARKERS = {
    "digital_arrest": (
        "digital arrest",
        "do not inform",
        "close fir",
        "money laundering",
        "senior officer",
        "verification payment",
        "security amount",
        "video call",
        "on video",
    ),
    "courier_scam": (
        "parcel no",
        "drugs detected",
        "custom department",
        "sim card parcel",
        "parcel blocked",
        "shipment blocked",
    ),
}


def _contains_keyword(text: str, keyword: str) -> bool:
    if " " in keyword or "-" in keyword:
        return keyword in text
    return re.search(rf"(?<![a-z0-9]){re.escape(keyword)}(?![a-z0-9])", text) is not None


def normalize_text(text: str) -> str:
    """Normalize scam text while preserving evidence-bearing tokens."""
    if text is None:
        return ""
    normalized = unicodedata.normalize("NFKC", text)
    normalized = normalized.replace("\u20b9", " rs ")
    normalized = re.sub(r"\s+", " ", normalized)
    normalized = normalized.strip().lower()
    return normalized


def prepare_model_text(text: str) -> str:
    """Add transparent domain markers for the Phase 1 hybrid baseline."""
    cleaned = normalize_text(text)
    markers = []
    for label, keywords in CATEGORY_MARKERS.items():
        for keyword in keywords:
            if _contains_keyword(cleaned, keyword):
                markers.append(f"__signal_{label}")
    for label, keywords in STRONG_CATEGORY_MARKERS.items():
        for keyword in keywords:
            if _contains_keyword(cleaned, keyword):
                markers.extend([f"__strong_signal_{label}"] * 4)
    if markers:
        return f"{cleaned} {' '.join(markers)}"
    return cleaned


def tokenize_for_display(text: str) -> list[str]:
    cleaned = normalize_text(text)
    if not cleaned:
        return []
    return cleaned.split()
