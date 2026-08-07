from dataclasses import dataclass
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
DATASET_PATH = DATA_DIR / "samples" / "phase2_dataset.csv"
MODELS_DIR = PROJECT_ROOT / "models"
OUTPUTS_DIR = PROJECT_ROOT / "outputs"
METRICS_DIR = OUTPUTS_DIR / "metrics"
DEMO_CASES_DIR = OUTPUTS_DIR / "demo_cases"
DB_PATH = PROJECT_ROOT / "fraudlens_cases.sqlite3"

@dataclass(frozen=True)
class ArtifactPaths:
    """The compact, versioned artifacts required by the TF-IDF predictor."""

    root: Path
    model: Path
    vectorizer: Path
    label_encoder: Path
    metrics: Path
    metadata: Path


def artifact_paths(root: Path = MODELS_DIR) -> ArtifactPaths:
    root = Path(root)
    return ArtifactPaths(
        root=root,
        model=root / "baseline_classifier.joblib",
        vectorizer=root / "vectorizer.joblib",
        label_encoder=root / "label_encoder.joblib",
        metrics=root / "metrics.json",
        metadata=root / "model_metadata.json",
    )


DEFAULT_ARTIFACTS = artifact_paths()
MODEL_PATH = DEFAULT_ARTIFACTS.model
VECTORIZER_PATH = DEFAULT_ARTIFACTS.vectorizer
LABEL_ENCODER_PATH = DEFAULT_ARTIFACTS.label_encoder
METRICS_PATH = DEFAULT_ARTIFACTS.metrics
METADATA_PATH = DEFAULT_ARTIFACTS.metadata

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
