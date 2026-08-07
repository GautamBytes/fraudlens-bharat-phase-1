from datetime import datetime, timezone
from pathlib import Path

import pytest
from pydantic import ValidationError

from fraudlens.analysis_service import AnalysisInput, AnalysisService, DatabaseCaseStore, create_analysis_service
from fraudlens.prediction import Prediction
from fraudlens.prediction import PredictorRegistry
from fraudlens.settings import Settings


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
    assert result.original_text == "Urgent KYC update"
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


@pytest.mark.parametrize(
    "analysis_input",
    [
        AnalysisInput(text=" \t\n "),
        AnalysisInput(text="x" * 20_001),
        AnalysisInput(text=123),
        AnalysisInput(text="urgent", user_notes="x" * 2_001),
    ],
)
def test_service_rejects_invalid_direct_input_at_the_service_boundary(analysis_input):
    service = _service(Prediction("unknown", 0.2, "rules", "v1", True))

    with pytest.raises(ValidationError):
        service.analyze(analysis_input)


def test_service_trims_direct_input_but_preserves_authoritative_storage_and_metadata():
    store = _RecordingStore()
    result = _service(Prediction("unknown", 0.2, "rules", "v1", True), store).analyze(
        AnalysisInput(
            text="  urgent verification  ",
            user_notes="  dashboard context  ",
            store_case=True,
            metadata={"stored": False, "origin": "dashboard"},
        )
    )

    assert result.original_text == "urgent verification"
    assert result.metadata["user_notes"] == "dashboard context"
    assert result.metadata["stored"] is True
    assert result.metadata["origin"] == "dashboard"


def test_service_returns_a_generic_storage_warning_when_persistence_fails():
    from fraudlens.analysis_service import AnalysisInput

    result = _service(
        Prediction("kyc_scam", 0.91, "tfidf_calibrated", "tfidf-v1", False),
        _RecordingStore(error=RuntimeError("/private/secrets.sqlite is unavailable")),
    ).analyze(AnalysisInput(text="Urgent KYC update", store_case=True))

    assert result.metadata["stored"] is False
    assert result.metadata["storage_warning"] == "Case storage was unavailable."
    assert "/private" not in result.metadata["storage_warning"]


def test_service_reports_expired_case_storage_as_a_generic_failure(tmp_path):
    store = DatabaseCaseStore(
        Path(tmp_path) / "expired.sqlite3",
        hmac_secret="test-secret",
        retention_days=1,
    )
    service = AnalysisService(
        predictor=_StubPredictor(
            Prediction("kyc_scam", 0.91, "tfidf_calibrated", "tfidf-v1", False)
        ),
        store=store,
        clock=lambda: datetime(2000, 1, 1, tzinfo=timezone.utc),
        id_generator=lambda: "expired-case",
    )

    result = service.analyze(AnalysisInput(text="Urgent KYC update", store_case=True))

    assert result.metadata["stored"] is False
    assert result.metadata["storage_warning"] == "Case storage was unavailable."
    assert "expired" not in result.metadata["storage_warning"].casefold()
    assert store.list_cases(10) == []


def test_legitimate_prediction_does_not_create_classifier_fraud_risk():
    from fraudlens.analysis_service import AnalysisInput

    result = _service(
        Prediction("legitimate", 0.99, "tfidf_calibrated", "tfidf-v1", False)
    ).analyze(AnalysisInput(text="Thank you for your order."))

    assert result.risk_level == "low"
    assert result.risk_score == 0
    assert not any(signal.name == "classifier_confidence" for signal in result.risk_signals)


def test_legitimate_result_has_a_neutral_complaint_draft():
    result = _service(
        Prediction("legitimate", 0.99, "tfidf_calibrated", "tfidf-v1", False)
    ).analyze(AnalysisInput(text="Thank you for your order."))

    assert "Classification: legitimate" in result.complaint_draft
    assert "no scam indicators from the classifier" in result.complaint_draft
    assert "official channel" in result.complaint_draft
    assert "Suspected fraud type" not in result.complaint_draft
    assert "1930" not in result.complaint_draft
    assert "NCRP" not in result.complaint_draft


def _settings(tmp_path, model_backend="tfidf"):
    return Settings(
        model_backend=model_backend,
        database_path=Path(tmp_path) / "cases.sqlite3",
        hmac_secret="test-secret",
        retention_days=30,
        store_cases_by_default=False,
        environment="test",
        allowed_hosts=(),
    )


def test_create_analysis_service_selects_the_configured_tfidf_predictor(tmp_path):
    selected = _StubPredictor(Prediction("unknown", 0.2, "tfidf-selected", "v1", True))
    service = create_analysis_service(
        settings=_settings(tmp_path),
        predictor_registry=PredictorRegistry({"tfidf": selected}),
    )

    result = service.analyze(AnalysisInput("Hello"))

    assert result.metadata["prediction_source"] == "tfidf-selected"


def test_create_analysis_service_rejects_an_unregistered_configured_backend(tmp_path):
    with pytest.raises(ValueError, match="Predictor configuration is unavailable"):
        create_analysis_service(
            settings=_settings(tmp_path, model_backend="muril"),
            predictor_registry=PredictorRegistry({}),
        )
