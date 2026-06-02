from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
DATASET_PATH = DATA_DIR / "samples" / "phase1_seed_dataset.csv"
MODELS_DIR = PROJECT_ROOT / "models"
OUTPUTS_DIR = PROJECT_ROOT / "outputs"
METRICS_DIR = OUTPUTS_DIR / "metrics"
DEMO_CASES_DIR = OUTPUTS_DIR / "demo_cases"
DB_PATH = PROJECT_ROOT / "fraudlens_cases.sqlite3"

MODEL_PATH = MODELS_DIR / "baseline_classifier.joblib"
VECTORIZER_PATH = MODELS_DIR / "vectorizer.joblib"
LABEL_ENCODER_PATH = MODELS_DIR / "label_encoder.joblib"
METRICS_PATH = MODELS_DIR / "metrics.json"

LABELS = [
    "kyc_scam",
    "digital_arrest",
    "fake_job",
    "investment_scam",
    "loan_scam",
    "courier_scam",
    "upi_refund_scam",
    "otp_phishing",
]

SHORTENER_DOMAINS = {
    "bit.ly",
    "tinyurl.com",
    "t.co",
    "goo.gl",
    "cutt.ly",
    "shorturl.at",
    "rebrand.ly",
    "is.gd",
    "ow.ly",
}

SUSPICIOUS_URL_KEYWORDS = {
    "kyc",
    "verify",
    "refund",
    "free",
    "bonus",
    "urgent",
    "login",
    "update",
    "blocked",
    "cashback",
    "claim",
    "support",
}

URGENCY_KEYWORDS = {
    "urgent",
    "immediately",
    "today",
    "now",
    "within",
    "expire",
    "last chance",
    "abhi",
    "turant",
    "jaldi",
    "midnight",
}

THREAT_KEYWORDS = {
    "block",
    "blocked",
    "freeze",
    "arrest",
    "warrant",
    "fir",
    "legal",
    "police",
    "court",
    "custody",
    "penalty",
    "delete",
    "suspend",
}

