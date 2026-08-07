import inspect
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from fraudlens import api
from fraudlens import config, database
from fraudlens.prediction import Prediction, PredictorRegistry
from fraudlens.settings import Settings


class _StubPredictor:
    def __init__(self, prediction):
        self._prediction = prediction

    def predict(self, text):
        return self._prediction


class _Store:
    def __init__(self, error=None):
        self.error = error
        self.initialized = 0
        self.saved = []

    def initialize(self):
        self.initialized += 1

    def save(self, result):
        if self.error:
            raise self.error
        self.saved.append(result)

    def list_cases(self, limit):
        return []

    def get_case(self, case_id):
        return None


def _settings(store_cases_by_default=False, allowed_hosts=()):
    return Settings(
        model_backend="tfidf",
        database_path=None,
        hmac_secret="test-secret",
        retention_days=30,
        store_cases_by_default=store_cases_by_default,
        environment="test",
        allowed_hosts=allowed_hosts,
    )


def _client(store_cases_by_default=False, store=None, allowed_hosts=()):
    app = api.create_app(
        settings=_settings(store_cases_by_default, allowed_hosts),
        predictor=_StubPredictor(Prediction("kyc_scam", 0.91, "test", "test-v1", False)),
        store=store or _Store(),
    )
    return app, TestClient(app)


def test_health_endpoint():
    app, test_client = _client()
    with test_client:
        response = test_client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"
        assert app.state.analysis_service is not None


def test_analyze_endpoint_returns_complete_result():
    _, test_client = _client()
    with test_client:
        response = test_client.post(
            "/analyze",
            json={"text": "Urgent KYC update required at http://bank-kyc-verify.example/login or account block today."},
        )
        assert response.status_code == 200
        payload = response.json()
        assert payload["predicted_label"] == "kyc_scam"
        assert payload["risk_level"] in {"low", "medium", "high"}
        assert isinstance(payload["entities"], list)
        assert payload["explanation"]


def test_analyze_endpoint_trims_request_text_and_user_notes():
    _, test_client = _client()
    with test_client:
        response = test_client.post(
            "/analyze",
            json={"text": "  urgent account verification  ", "user_notes": "  called the sender  "},
        )

        assert response.status_code == 200
        assert response.json()["original_text"] == "urgent account verification"
        assert response.json()["metadata"]["user_notes"] == "called the sender"


def test_analyze_endpoint_rejects_whitespace_only_text():
    _, test_client = _client()
    with test_client:
        response = test_client.post("/analyze", json={"text": " \t\n "})
        assert response.status_code == 422


def test_analyze_endpoint_rejects_overlong_text():
    _, test_client = _client()
    with test_client:
        response = test_client.post("/analyze", json={"text": "x" * 20_001})
        assert response.status_code == 422


def test_analyze_endpoint_rejects_unknown_fields():
    _, test_client = _client()
    with test_client:
        response = test_client.post(
            "/analyze",
            json={"text": "urgent verification", "unexpected": "not accepted"},
        )
        assert response.status_code == 422


def test_analyze_endpoint_converts_whitespace_only_user_notes_to_none():
    _, test_client = _client()
    with test_client:
        response = test_client.post(
            "/analyze",
            json={"text": "urgent verification", "user_notes": " \n\t "},
        )

        assert response.status_code == 200
        assert response.json()["metadata"]["user_notes"] is None


def test_analyze_endpoint_rejects_overlong_user_notes():
    _, test_client = _client()
    with test_client:
        response = test_client.post(
            "/analyze",
            json={"text": "urgent verification", "user_notes": "x" * 2_001},
        )
        assert response.status_code == 422


def test_analyze_storage_uses_the_safe_default_unless_explicitly_requested():
    store = _Store()
    _, test_client = _client(store=store)
    with test_client:
        response = test_client.post("/analyze", json={"text": "urgent verification"})
        assert response.status_code == 200
        assert response.json()["metadata"]["stored"] is False
        assert store.saved == []

        response = test_client.post(
            "/analyze", json={"text": "urgent verification", "store_case": True}
        )
        assert response.status_code == 200
        assert response.json()["metadata"]["stored"] is True
        assert len(store.saved) == 1


def test_analyze_storage_uses_true_runtime_default_when_omitted():
    store = _Store()
    _, test_client = _client(store_cases_by_default=True, store=store)
    with test_client:
        response = test_client.post("/analyze", json={"text": "urgent verification"})

    assert response.status_code == 200
    assert response.json()["metadata"]["stored"] is True
    assert len(store.saved) == 1


def test_analyze_handles_storage_failure_without_leaking_details():
    _, test_client = _client(store=_Store(error=RuntimeError("/private/cases.sqlite3 failed")))
    with test_client:
        response = test_client.post(
            "/analyze", json={"text": "urgent verification", "store_case": True}
        )

    assert response.status_code == 200
    assert response.json()["metadata"]["stored"] is False
    assert response.json()["metadata"]["storage_warning"] == "Case storage was unavailable."
    assert "/private" not in response.text


def test_cases_limit_and_security_headers_are_constrained():
    _, test_client = _client()
    with test_client:
        for limit in (0, 101):
            assert test_client.get("/cases", params={"limit": limit}).status_code == 422
        response = test_client.get("/health")

    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["cache-control"] == "no-store"


def test_allowed_hosts_are_enabled_only_when_configured():
    _, test_client = _client(allowed_hosts=("testserver",))
    with test_client:
        assert test_client.get("/health").status_code == 200
        assert test_client.get("/health", headers={"host": "untrusted.example"}).status_code == 400


def test_api_uses_lifespan_instead_of_deprecated_startup_events():
    assert ".on_event(" not in inspect.getsource(api)


def test_default_api_store_persists_only_to_the_configured_database_path(tmp_path):
    configured_path = Path(tmp_path) / "configured.sqlite3"
    settings = Settings(
        model_backend="tfidf",
        database_path=configured_path,
        hmac_secret="test-secret",
        retention_days=30,
        store_cases_by_default=True,
        environment="test",
        allowed_hosts=(),
    )
    application = api.create_app(
        settings=settings,
        predictor=_StubPredictor(Prediction("kyc_scam", 0.91, "test", "test-v1", False)),
    )

    with TestClient(application) as test_client:
        response = test_client.post("/analyze", json={"text": "urgent verification"})
        listed = test_client.get("/cases")

    case_id = response.json()["case_id"]
    assert response.status_code == 200
    assert response.json()["metadata"]["stored"] is True
    assert configured_path.exists()
    assert [case["case_id"] for case in listed.json()] == [case_id]
    assert database.get_case(case_id, path=config.DB_PATH) is None


def test_analyze_message_uses_the_settings_default_when_storage_is_omitted(monkeypatch, tmp_path):
    settings = Settings(
        model_backend="tfidf",
        database_path=Path(tmp_path) / "compat.sqlite3",
        hmac_secret="test-secret",
        retention_days=30,
        store_cases_by_default=True,
        environment="test",
        allowed_hosts=(),
    )
    captured = []

    class _Service:
        def analyze(self, analysis_input):
            captured.append(analysis_input)
            return "result"

    monkeypatch.setattr(api.Settings, "from_env", lambda: settings)
    monkeypatch.setattr(api, "create_analysis_service", lambda *, settings: _Service())

    assert api.analyze_message("message") == "result"
    assert captured[-1].store_case is True
    assert api.analyze_message("message", store_case=False) == "result"
    assert captured[-1].store_case is False


def test_create_app_rejects_an_unregistered_configured_backend(tmp_path):
    settings = Settings(
        model_backend="muril",
        database_path=Path(tmp_path) / "cases.sqlite3",
        hmac_secret="test-secret",
        retention_days=30,
        store_cases_by_default=False,
        environment="test",
        allowed_hosts=(),
    )

    with pytest.raises(ValueError, match="Application configuration is invalid"):
        api.create_app(settings=settings, predictor_registry=PredictorRegistry({}))
