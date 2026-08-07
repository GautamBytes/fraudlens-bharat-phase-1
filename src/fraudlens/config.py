import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping


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
    """The compact artifacts and tracked trust manifest required by the predictor."""

    root: Path
    model: Path
    vectorizer: Path
    label_encoder: Path
    metrics: Path
    metadata: Path
    manifest: Path


def artifact_paths(root: Path = MODELS_DIR) -> ArtifactPaths:
    root = Path(root)
    return ArtifactPaths(
        root=root,
        model=root / "baseline_classifier.joblib",
        vectorizer=root / "vectorizer.joblib",
        label_encoder=root / "label_encoder.joblib",
        metrics=root / "metrics.json",
        metadata=root / "model_metadata.json",
        manifest=root / "artifact_manifest.json",
    )


DEFAULT_ARTIFACTS = artifact_paths()
MODEL_PATH = DEFAULT_ARTIFACTS.model
VECTORIZER_PATH = DEFAULT_ARTIFACTS.vectorizer
LABEL_ENCODER_PATH = DEFAULT_ARTIFACTS.label_encoder
METRICS_PATH = DEFAULT_ARTIFACTS.metrics
METADATA_PATH = DEFAULT_ARTIFACTS.metadata
ARTIFACT_MANIFEST_PATH = DEFAULT_ARTIFACTS.manifest

# This canonical input is part of the release trust anchor. Changing training
# behaviour changes this hash and requires retraining and a new manifest.
TRAINING_CONFIGURATION: Mapping[str, Any] = {
    "backend": "tfidf",
    "vectorizer": {
        "ngram_range": [1, 2],
        "min_df": 1,
        "max_features": 5000,
        "sublinear_tf": True,
    },
    "classifier": {
        "type": "CalibratedClassifierCV",
        "estimator": "LogisticRegression",
        "max_iter": 1000,
        "class_weight": "balanced",
        "random_state": 42,
        "calibration_method": "sigmoid",
        "calibration_cv": 3,
    },
    "threshold": {
        "selection_split": "validation",
        "objective": "maximise correct-minus-incorrect coverage",
    },
}
ARTIFACT_MANIFEST_VERSION = 1
ARTIFACT_FILENAMES = (
    "baseline_classifier.joblib",
    "vectorizer.joblib",
    "label_encoder.joblib",
    "model_metadata.json",
    "metrics.json",
)


def canonical_sha256(value: Mapping[str, Any]) -> str:
    """Hash a JSON-compatible value using the deterministic release encoding."""
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def training_configuration_sha256() -> str:
    return canonical_sha256(TRAINING_CONFIGURATION)


def model_training_code_sha256() -> str:
    """Bind trusted artifacts to this exact trainer source, never to a pickle alone."""
    return hashlib.sha256((Path(__file__).parent / "model_training.py").read_bytes()).hexdigest()


def release_model_version(dataset_sha256: str, configuration_sha256: str, code_sha256: str) -> str:
    return "tfidf-calibrated-{}-{}-{}".format(
        dataset_sha256[:12], configuration_sha256[:12], code_sha256[:12]
    )

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
