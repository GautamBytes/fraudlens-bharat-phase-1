"""Inference for the persisted calibrated TF-IDF model with an honest fallback."""

from __future__ import annotations

import json
from typing import Dict, Tuple

from fraudlens.config import ArtifactPaths, DEFAULT_ARTIFACTS
from fraudlens.prediction import Prediction, Predictor, PredictorRegistry
from fraudlens.preprocessing import normalize_text


RULE_KEYWORDS: Dict[str, tuple] = {
    "kyc_scam": ("kyc", "pan", "aadhaar", "account block", "wallet freeze", "ekyc"),
    "digital_arrest": (
        "digital arrest", "arrest", "warrant", "cbi", "cyber cell", "court",
        "money laundering", "do not inform", "do not disconnect", "fir case",
    ),
    "fake_job": ("registration fee", "joining fee", "pay to start", "work from home task"),
    "investment_scam": ("guaranteed profit", "double your money", "2x return", "crypto vip"),
    "loan_scam": ("processing fee", "file charge", "insurance fee", "instant approval"),
    "courier_scam": (
        "parcel no", "fedex", "dhl", "custom department", "sim card parcel", "parcel blocked",
    ),
    "upi_refund_scam": ("collect request", "upi pin", "scan qr", "refund cashback"),
    "otp_phishing": ("share otp", "send otp", "otp to verify", "share cvv", "share pin"),
}
RULE_FALLBACK_VERSION = "rule-fallback-v1"


class ModelPredictor(Predictor):
    """Lazy, calibrated predictor that abstains below its saved validation threshold."""

    def __init__(self, artifacts: ArtifactPaths = DEFAULT_ARTIFACTS):
        self._artifacts = artifacts
        self._loaded = False
        self._classifier = None
        self._vectorizer = None
        self._label_encoder = None
        self._metadata = None

    def _load(self) -> None:
        if self._loaded:
            return
        self._loaded = True
        required = (
            self._artifacts.model,
            self._artifacts.vectorizer,
            self._artifacts.label_encoder,
            self._artifacts.metadata,
        )
        if not all(path.exists() for path in required):
            return
        try:
            import joblib

            metadata = json.loads(self._artifacts.metadata.read_text(encoding="utf-8"))
            threshold = float(metadata["threshold"])
            model_version = str(metadata["model_version"])
            if not 0.0 <= threshold <= 1.0 or not model_version:
                raise ValueError("invalid calibrated model metadata")
            self._classifier = joblib.load(self._artifacts.model)
            self._vectorizer = joblib.load(self._artifacts.vectorizer)
            self._label_encoder = joblib.load(self._artifacts.label_encoder)
            self._metadata = metadata
        except Exception:
            self._classifier = None
            self._vectorizer = None
            self._label_encoder = None
            self._metadata = None

    def predict(self, text: str) -> Prediction:
        cleaned = normalize_text(text)
        self._load()
        if self._artifacts_loaded():
            try:
                vector = self._vectorizer.transform([cleaned])
                probabilities = self._classifier.predict_proba(vector)[0]
                encoded_label = int(probabilities.argmax())
                label = str(self._label_encoder.inverse_transform([encoded_label])[0])
                raw_confidence = float(max(probabilities))
                confidence = round(raw_confidence, 4)
                threshold = float(self._metadata["threshold"])
                model_version = str(self._metadata["model_version"])
                if raw_confidence < threshold:
                    return Prediction(
                        label="unknown",
                        confidence=confidence,
                        source="tfidf_calibrated_abstained",
                        model_version=model_version,
                        abstained=True,
                    )
                return Prediction(
                    label=label,
                    confidence=confidence,
                    source="tfidf_calibrated",
                    model_version=model_version,
                    abstained=False,
                )
            except Exception:
                # A damaged in-memory artifact must never produce a partial model answer.
                self._classifier = None
                self._vectorizer = None
                self._label_encoder = None
                self._metadata = None
        label, confidence = rule_based_predict(cleaned)
        return Prediction(
            label=label,
            confidence=confidence,
            source="rule_fallback",
            model_version=RULE_FALLBACK_VERSION,
            abstained=label == "unknown",
        )

    def _artifacts_loaded(self) -> bool:
        return all(
            value is not None
            for value in (self._classifier, self._vectorizer, self._label_encoder, self._metadata)
        )


def rule_based_predict(text: str) -> Tuple[str, float]:
    """Use rules only when several specific scam cues agree; otherwise abstain."""
    cleaned = normalize_text(text)
    scores = {
        label: sum(1 for keyword in keywords if keyword in cleaned)
        for label, keywords in RULE_KEYWORDS.items()
    }
    best_label = max(scores, key=scores.get)
    best_score = scores[best_label]
    # A single broad word has too many benign meanings to make a fraud claim.
    if best_score < 2:
        return "unknown", 0.2
    return best_label, round(min(0.45 + best_score * 0.12, 0.9), 4)


predictor = ModelPredictor()
predictor_registry = PredictorRegistry({"tfidf": predictor})
