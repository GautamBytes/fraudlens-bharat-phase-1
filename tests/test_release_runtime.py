import json
import logging
import re

from fastapi.testclient import TestClient

from fraudlens import __version__
from fraudlens.api import create_app
from fraudlens.prediction import Prediction
from fraudlens.settings import Settings


class _Predictor:
    def predict(self, text):
        return Prediction("unknown", 0.2, "test", "test-v1", True)


class _ReadyStore:
    def __init__(self, readiness_error=None):
        self.readiness_error = readiness_error
        self.readiness_checks = 0

    def initialize(self):
        pass

    def healthcheck(self):
        self.readiness_checks += 1
        if self.readiness_error is not None:
            raise self.readiness_error

    def save(self, result):
        pass

    def list_cases(self, limit):
        return []

    def get_case(self, case_id):
        return None

    def delete(self, case_id):
        return False

    def clear(self):
        return 0

    def entity_graph(self, minimum_case_count=2, case_limit=100, max_edges=1_000):
        raise AssertionError("not used")


def _settings():
    return Settings(
        model_backend="tfidf",
        database_path=None,
        hmac_secret="test-secret",
        retention_days=30,
        store_cases_by_default=False,
        environment="test",
        allowed_hosts=(),
    )


def _client(store):
    return TestClient(create_app(settings=_settings(), predictor=_Predictor(), store=store))


def test_release_identity_is_consistent():
    assert __version__ == "1.0.0"
    with _client(_ReadyStore()) as client:
        schema = client.get("/openapi.json").json()
        assert schema["info"]["title"] == "FraudLens Bharat API"
        assert schema["info"]["version"] == __version__
        assert "Phase 1" not in schema["info"]["description"]
        assert client.get("/health").json() == {
            "status": "ok",
            "service": "fraudlens-bharat",
            "version": __version__,
        }


def test_readiness_checks_storage_and_returns_version():
    store = _ReadyStore()
    with _client(store) as client:
        response = client.get("/ready")
    assert response.status_code == 200
    assert response.json() == {
        "status": "ready",
        "service": "fraudlens-bharat",
        "version": __version__,
    }
    assert store.readiness_checks == 1


def test_readiness_failure_is_generic_and_does_not_affect_liveness():
    secret_path = "/private/customer/cases.sqlite3"
    store = _ReadyStore(RuntimeError(secret_path))
    with _client(store) as client:
        readiness = client.get("/ready")
        liveness = client.get("/health")
    assert readiness.status_code == 503
    assert readiness.json() == {"detail": "Service not ready"}
    assert secret_path not in readiness.text
    assert liveness.status_code == 200


def test_request_log_uses_route_template_and_excludes_sensitive_inputs(caplog):
    raw_text = "SECRET OTP 123456"
    raw_notes = "customer phone +91 9999999999"
    raw_case_id = "private-case-identifier"
    caplog.set_level(logging.INFO, logger="fraudlens.request")

    with _client(_ReadyStore()) as client:
        response = client.post(
            "/analyze?tracking=secret-query",
            json={"text": raw_text, "user_notes": raw_notes},
            headers={"authorization": "Bearer secret-header"},
        )
        missing = client.get("/cases/{}".format(raw_case_id))

    assert response.status_code == 200
    assert missing.status_code == 404
    request_ids = [response.headers["x-request-id"], missing.headers["x-request-id"]]
    assert len(set(request_ids)) == 2
    assert all(re.fullmatch(r"[0-9a-f]{32}", request_id) for request_id in request_ids)

    events = [json.loads(record.message) for record in caplog.records]
    assert {event["route"] for event in events} >= {"/analyze", "/cases/{case_id}"}
    assert all(set(event) == {"event", "method", "request_id", "route", "status_code"} for event in events)
    combined = "\n".join(record.message for record in caplog.records)
    for secret in (raw_text, raw_notes, raw_case_id, "secret-query", "secret-header"):
        assert secret not in combined


def test_unmatched_paths_are_not_written_to_request_logs(caplog):
    caplog.set_level(logging.INFO, logger="fraudlens.request")
    with _client(_ReadyStore()) as client:
        response = client.get("/missing/SECRET-PATH-COMPONENT")
    assert response.status_code == 404
    event = json.loads(caplog.records[-1].message)
    assert event["route"] == "<unmatched>"
    assert "SECRET-PATH-COMPONENT" not in caplog.records[-1].message
