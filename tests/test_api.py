import inspect

from fastapi.testclient import TestClient

from fraudlens import api
from fraudlens.prediction import Prediction
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
