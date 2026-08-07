"""Inference for the persisted calibrated TF-IDF model with an honest fallback."""

from __future__ import annotations

import json
import hashlib
from pathlib import Path
from typing import Any, Dict, Mapping, Tuple

from fraudlens.config import (
    ARTIFACT_FILENAMES,
    ARTIFACT_MANIFEST_VERSION,
    ArtifactPaths,
    DEFAULT_ARTIFACTS,
    model_training_code_sha256,
    release_model_version,
    training_configuration_sha256,
)
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


def _file_sha256(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _strict_object(value: Any, keys: set[str], name: str) -> Mapping[str, Any]:
    if not isinstance(value, dict) or set(value) != keys:
        raise ValueError("invalid {}".format(name))
    return value


def _verified_metadata(artifacts: ArtifactPaths) -> Dict[str, Any]:
    """Validate the release trust anchor before any pickle/joblib deserialization."""
    paths = {
        artifacts.model.name: artifacts.model,
        artifacts.vectorizer.name: artifacts.vectorizer,
        artifacts.label_encoder.name: artifacts.label_encoder,
        artifacts.metadata.name: artifacts.metadata,
        artifacts.metrics.name: artifacts.metrics,
    }
    if tuple(paths) != ARTIFACT_FILENAMES or not artifacts.manifest.exists():
        raise ValueError("unexpected trusted artifact layout")
    if not all(path.exists() for path in paths.values()):
        raise ValueError("missing trusted artifact")

    manifest = _strict_object(
        json.loads(artifacts.manifest.read_text(encoding="utf-8")),
        {
            "schema_version",
            "trust_anchor",
            "artifacts",
            "dataset",
            "model_version",
            "training_configuration_sha256",
            "model_training_code_sha256",
            "runtime_versions",
        },
        "artifact manifest",
    )
    if (
        manifest["schema_version"] != ARTIFACT_MANIFEST_VERSION
        or manifest["trust_anchor"] != "tracked-release-artifact-manifest"
        or not isinstance(manifest["model_version"], str)
    ):
        raise ValueError("invalid artifact manifest header")
    manifest_artifacts = _strict_object(manifest["artifacts"], set(ARTIFACT_FILENAMES), "artifact hashes")
    for name, path in paths.items():
        digest = _strict_object(manifest_artifacts[name], {"sha256"}, "artifact hash")["sha256"]
        if not isinstance(digest, str) or len(digest) != 64 or digest != _file_sha256(path):
            raise ValueError("artifact integrity check failed")

    dataset = _strict_object(manifest["dataset"], {"filename", "sha256", "rows"}, "dataset metadata")
    if (
        not isinstance(dataset["filename"], str)
        or not isinstance(dataset["sha256"], str)
        or len(dataset["sha256"]) != 64
        or not isinstance(dataset["rows"], int)
        or dataset["rows"] <= 0
    ):
        raise ValueError("invalid dataset metadata")
    if manifest["training_configuration_sha256"] != training_configuration_sha256():
        raise ValueError("training configuration has changed")
    if manifest["model_training_code_sha256"] != model_training_code_sha256():
        raise ValueError("training code has changed")
    runtime_versions = _strict_object(
        manifest["runtime_versions"], {"python", "sklearn", "joblib"}, "runtime provenance"
    )
    if not all(isinstance(value, str) and value for value in runtime_versions.values()):
        raise ValueError("invalid runtime provenance")
    expected_version = release_model_version(
        dataset["sha256"], manifest["training_configuration_sha256"], manifest["model_training_code_sha256"]
    )
    if manifest["model_version"] != expected_version:
        raise ValueError("model version does not bind provenance")

    metadata = json.loads(artifacts.metadata.read_text(encoding="utf-8"))
    metrics = json.loads(artifacts.metrics.read_text(encoding="utf-8"))
    if not isinstance(metadata, dict) or not isinstance(metrics, dict):
        raise ValueError("invalid artifact metadata")
    for values in (metadata, metrics):
        if (
            values.get("model_version") != expected_version
            or values.get("dataset_sha256") != dataset["sha256"]
            or values.get("training_configuration_sha256") != manifest["training_configuration_sha256"]
            or values.get("model_training_code_sha256") != manifest["model_training_code_sha256"]
        ):
            raise ValueError("artifact provenance mismatch")
    if (
        metadata.get("dataset_filename") != dataset["filename"]
        or metadata.get("dataset_rows") != dataset["rows"]
        or metadata.get("runtime_versions") != runtime_versions
    ):
        raise ValueError("metadata does not match manifest")
    threshold = metadata.get("threshold")
    if not isinstance(threshold, (int, float)) or not 0.0 <= float(threshold) <= 1.0:
        raise ValueError("invalid calibrated model metadata")
    return metadata


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
        try:
            import joblib

            metadata = _verified_metadata(self._artifacts)
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
