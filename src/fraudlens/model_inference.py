from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Tuple

from fraudlens.config import LABEL_ENCODER_PATH, MODEL_PATH, VECTORIZER_PATH
from fraudlens.preprocessing import normalize_text, prepare_model_text


RULE_KEYWORDS: Dict[str, tuple[str, ...]] = {
    "kyc_scam": ("kyc", "pan", "aadhaar", "account block", "wallet freeze", "ekyc"),
    "digital_arrest": ("digital arrest", "arrest", "warrant", "cbi", "cyber cell", "court", "money laundering"),
    "fake_job": ("job", "salary", "registration fee", "joining", "hr", "work from home", "task"),
    "investment_scam": ("investment", "crypto", "trading", "double", "guaranteed return", "profit", "vip"),
    "loan_scam": ("loan", "processing fee", "cibil", "disbursal", "recovery", "instant approval"),
    "courier_scam": ("parcel", "courier", "customs", "fedex", "dhl", "shipment", "delivery"),
    "upi_refund_scam": ("refund", "cashback", "collect request", "receive money", "upi pin", "qr"),
    "otp_phishing": ("otp", "password", "cvv", "pin", "verification code", "login attempt"),
}


@dataclass
class Prediction:
    label: str
    confidence: float
    source: str


class ModelPredictor:
    def __init__(self):
        self._loaded = False
        self._classifier = None
        self._vectorizer = None
        self._label_encoder = None

    def _load(self) -> None:
        if self._loaded:
            return
        self._loaded = True
        if not (MODEL_PATH.exists() and VECTORIZER_PATH.exists() and LABEL_ENCODER_PATH.exists()):
            return
        try:
            import joblib

            self._classifier = joblib.load(MODEL_PATH)
            self._vectorizer = joblib.load(VECTORIZER_PATH)
            self._label_encoder = joblib.load(LABEL_ENCODER_PATH)
        except Exception:
            self._classifier = None
            self._vectorizer = None
            self._label_encoder = None

    def predict(self, text: str) -> Prediction:
        cleaned = normalize_text(text)
        self._load()
        if self._classifier is not None and self._vectorizer is not None and self._label_encoder is not None:
            try:
                vector = self._vectorizer.transform([prepare_model_text(cleaned)])
                encoded_label = self._classifier.predict(vector)[0]
                label = self._label_encoder.inverse_transform([encoded_label])[0]
                if hasattr(self._classifier, "predict_proba"):
                    confidence = float(max(self._classifier.predict_proba(vector)[0]))
                else:
                    confidence = 0.7
                rule_label, rule_confidence = rule_based_predict(cleaned)
                if rule_label == label:
                    confidence = max(confidence, rule_confidence)
                    source = "baseline_model_with_rule_agreement"
                elif confidence < 0.45 and rule_confidence > confidence:
                    label = rule_label
                    confidence = rule_confidence
                    source = "rule_fallback_low_model_confidence"
                else:
                    source = "baseline_model"
                return Prediction(label=label, confidence=round(confidence, 4), source=source)
            except Exception:
                pass
        label, confidence = rule_based_predict(cleaned)
        return Prediction(label=label, confidence=confidence, source="rule_fallback")


def rule_based_predict(text: str) -> Tuple[str, float]:
    cleaned = normalize_text(text)
    scores: Dict[str, int] = {}
    for label, keywords in RULE_KEYWORDS.items():
        scores[label] = sum(1 for keyword in keywords if keyword in cleaned)
    best_label = max(scores, key=scores.get)
    best_score = scores[best_label]
    if best_score == 0:
        return "unknown", 0.2
    confidence = min(0.45 + best_score * 0.12, 0.9)
    return best_label, round(confidence, 4)


predictor = ModelPredictor()
