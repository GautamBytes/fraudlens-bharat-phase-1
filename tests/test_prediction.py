import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import pytest

from fraudlens.config import artifact_paths
from fraudlens.model_inference import ModelPredictor, rule_based_predict
from fraudlens.model_training import train_baseline
from fraudlens.prediction import Prediction, PredictorRegistry


class _FixedVectorizer:
    def transform(self, texts):
        return list(texts)


class _FixedClassifier:
    def predict(self, texts):
        return [0 for _ in texts]

    def predict_proba(self, texts):
        return np.array([[0.96, 0.04] for _ in texts])


class _FixedEncoder:
    def inverse_transform(self, labels):
        return ["legitimate" for _ in labels]


class _StubPredictor:
    def __init__(self, prediction):
        self.prediction = prediction

    def predict(self, text):
        return self.prediction


def test_low_confidence_model_prediction_abstains():
    predictor = ModelPredictor()
    predictor._loaded = True
    predictor._classifier = _FixedClassifier()
    predictor._vectorizer = _FixedVectorizer()
    predictor._label_encoder = _FixedEncoder()
    predictor._metadata = {"threshold": 0.97, "model_version": "test-v1"}

    prediction = predictor.predict("This looks like ordinary discussion.")

    assert prediction == Prediction(
        label="unknown",
        confidence=0.96,
        source="tfidf_calibrated_abstained",
        model_version="test-v1",
        abstained=True,
    )


def test_high_confidence_legitimate_model_prediction_is_not_rewritten_by_rules():
    predictor = ModelPredictor()
    predictor._loaded = True
    predictor._classifier = _FixedClassifier()
    predictor._vectorizer = _FixedVectorizer()
    predictor._label_encoder = _FixedEncoder()
    predictor._metadata = {"threshold": 0.9, "model_version": "test-v1"}

    prediction = predictor.predict("Please send the project OTP document by email.")

    assert prediction.label == "legitimate"
    assert prediction.abstained is False
    assert prediction.source == "tfidf_calibrated"


def test_registry_selects_injected_predictor_and_rejects_unknown_backend():
    expected = Prediction("legitimate", 0.99, "test", "v1", False)
    registry = PredictorRegistry({"stub": _StubPredictor(expected)})

    assert registry.get("stub").predict("anything") == expected
    with pytest.raises(ValueError, match="Unsupported predictor backend"):
        registry.get("not-a-backend")


@pytest.mark.parametrize(
    "text",
    [
        "I need a home loan; what documents are required?",
        "Please send the project OTP document by email.",
        "Parcel delivered successfully. Thank you.",
    ],
)
def test_rule_fallback_does_not_call_benign_keyword_collisions_scam(text):
    label, confidence = rule_based_predict(text)

    assert (label, confidence) == ("unknown", 0.2)


def test_missing_or_corrupt_artifacts_use_abstaining_rule_fallback(tmp_path):
    paths = artifact_paths(tmp_path)
    paths.model.write_bytes(b"not a joblib model")

    prediction = ModelPredictor(artifacts=paths).predict("Parcel delivered successfully. Thank you.")

    assert prediction.label == "unknown"
    assert prediction.abstained is True
    assert prediction.source == "rule_fallback"
    assert prediction.model_version == "rule-fallback-v1"


def test_training_writes_honest_metadata_and_keeps_validation_and_test_out_of_vocabulary(tmp_path):
    project_root = Path(__file__).resolve().parents[1]
    dataset = pd.read_csv(project_root / "data" / "samples" / "phase2_dataset.csv")
    validation_index = dataset.index[dataset["split"] == "validation"][0]
    test_index = dataset.index[dataset["split"] == "test"][0]
    dataset.loc[validation_index, "text"] += " validationonlytoken"
    dataset.loc[test_index, "text"] += " testonlytoken"
    dataset_path = tmp_path / "phase2.csv"
    dataset.to_csv(dataset_path, index=False)

    metrics = train_baseline(dataset_path=dataset_path, artifact_dir=tmp_path, backend="tfidf")
    paths = artifact_paths(tmp_path)
    metadata = json.loads(paths.metadata.read_text(encoding="utf-8"))
    vectorizer = joblib.load(paths.vectorizer)

    assert metrics["split_rows"] == {"train": 48, "validation": 8, "test": 8}
    assert metadata["present_labels"] == [
        "courier_scam", "digital_arrest", "fake_job", "investment_scam",
        "kyc_scam", "loan_scam", "otp_phishing", "upi_refund_scam",
    ]
    assert metadata["missing_labels"] == ["legitimate"]
    assert metadata["phase2_target_met"] is False
    assert metadata["threshold"] >= 0.0
    assert metadata["dataset_sha256"]
    assert metadata["model_version"].startswith("tfidf-calibrated-")
    assert metadata["calibration"]["training_only"] is True
    assert metadata["evaluation"]["frozen_test_split"] is True
    split_ids = metadata["split_ids"]
    assert not set(split_ids["train"]).intersection(split_ids["validation"])
    assert not set(split_ids["train"]).intersection(split_ids["test"])
    assert not set(split_ids["validation"]).intersection(split_ids["test"])
    assert "validationonlytoken" not in vectorizer.vocabulary_
    assert "testonlytoken" not in vectorizer.vocabulary_


def test_training_rejects_unsupported_backend(tmp_path):
    project_root = Path(__file__).resolve().parents[1]

    with pytest.raises(ValueError, match="Unsupported backend"):
        train_baseline(
            dataset_path=project_root / "data" / "samples" / "phase2_dataset.csv",
            artifact_dir=tmp_path,
            backend="rules",
        )


def test_training_artifacts_are_byte_deterministic(tmp_path):
    project_root = Path(__file__).resolve().parents[1]
    dataset_path = project_root / "data" / "samples" / "phase2_dataset.csv"
    first = tmp_path / "first"
    second = tmp_path / "second"

    train_baseline(dataset_path=dataset_path, artifact_dir=first)
    train_baseline(dataset_path=dataset_path, artifact_dir=second)

    first_paths = artifact_paths(first)
    second_paths = artifact_paths(second)
    for name in ("model", "vectorizer", "label_encoder", "metrics", "metadata"):
        assert getattr(first_paths, name).read_bytes() == getattr(second_paths, name).read_bytes()
    assert joblib.load(first_paths.vectorizer)._stop_words_id == 0
