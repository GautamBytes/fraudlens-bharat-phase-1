from datetime import datetime

from fraudlens.prediction import Prediction


class _StubPredictor:
    def __init__(self, prediction):
        self.prediction = prediction
        self.seen_text = None

    def predict(self, text):
        self.seen_text = text
        return self.prediction


class _RecordingStore:
    def __init__(self, error=None):
        self.error = error
        self.saved = []

    def save(self, result):
        if self.error:
            raise self.error
        self.saved.append(result)


def _service(prediction, store=None):
    from fraudlens.analysis_service import AnalysisService

    return AnalysisService(
        predictor=_StubPredictor(prediction),
        store=store,
        clock=lambda: datetime(2026, 8, 7, 12, 0, 0),
        id_generator=lambda: "case-123",
    )


def test_service_returns_authoritative_metadata_without_storing_by_default():
    from fraudlens.analysis_service import AnalysisInput

    store = _RecordingStore()
    result = _service(
        Prediction("kyc_scam", 0.91, "tfidf_calibrated", "tfidf-v1", False), store
    ).analyze(
        AnalysisInput(
            text="  Urgent KYC update  ",
            user_notes="called sender",
            metadata={
                "prediction_source": "untrusted",
                "stored": True,
                "campaign": "dashboard",
            },
        )
    )

    assert result.case_id == "case-123"
    assert result.created_at == datetime(2026, 8, 7, 12, 0, 0)
    assert result.original_text == "  Urgent KYC update  "
    assert result.metadata == {
        "prediction_source": "tfidf_calibrated",
        "prediction_model_version": "tfidf-v1",
        "prediction_abstained": False,
        "user_notes": "called sender",
        "stored": False,
        "campaign": "dashboard",
    }
    assert store.saved == []


def test_service_persists_only_after_a_successful_save():
    from fraudlens.analysis_service import AnalysisInput

    store = _RecordingStore()
    result = _service(
        Prediction("kyc_scam", 0.91, "tfidf_calibrated", "tfidf-v1", False), store
    ).analyze(AnalysisInput(text="Urgent KYC update", store_case=True))

    assert result.metadata["stored"] is True
    assert store.saved == [result]


def test_service_returns_a_generic_storage_warning_when_persistence_fails():
    from fraudlens.analysis_service import AnalysisInput

    result = _service(
        Prediction("kyc_scam", 0.91, "tfidf_calibrated", "tfidf-v1", False),
        _RecordingStore(error=RuntimeError("/private/secrets.sqlite is unavailable")),
    ).analyze(AnalysisInput(text="Urgent KYC update", store_case=True))

    assert result.metadata["stored"] is False
    assert result.metadata["storage_warning"] == "Case storage was unavailable."
    assert "/private" not in result.metadata["storage_warning"]


def test_legitimate_prediction_does_not_create_classifier_fraud_risk():
    from fraudlens.analysis_service import AnalysisInput

    result = _service(
        Prediction("legitimate", 0.99, "tfidf_calibrated", "tfidf-v1", False)
    ).analyze(AnalysisInput(text="Thank you for your order."))

    assert result.risk_level == "low"
    assert result.risk_score == 0
    assert not any(signal.name == "classifier_confidence" for signal in result.risk_signals)
