import asyncio
import inspect
import sqlite3
from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from fraudlens import api
from fraudlens import config, database
from fraudlens.graph_analysis import EntityLink, build_entity_graph
from fraudlens.ocr import (
    ImageTooLargeError,
    InvalidImageError,
    NoTextDetectedError,
    OcrError,
    OcrResult,
    OcrTimeoutError,
    OcrUnavailableError,
)
from fraudlens.prediction import Prediction, PredictorRegistry
from fraudlens.settings import Settings


class _StubPredictor:
    def __init__(self, prediction):
        self._prediction = prediction

    def predict(self, text):
        return self._prediction


class _Store:
    def __init__(self, error=None, case_ids=()):
        self.error = error
        self.initialized = 0
        self.saved = []
        self.case_ids = set(case_ids)
        self.graph_calls = []
        self.graph_result = _graph_result()

    def initialize(self):
        self.initialized += 1

    def healthcheck(self):
        if self.error:
            raise self.error

    def save(self, result):
        if self.error:
            raise self.error
        self.saved.append(result)

    def list_cases(self, limit):
        return []

    def get_case(self, case_id):
        return None

    def delete(self, case_id):
        if self.error:
            raise self.error
        if case_id not in self.case_ids:
            return False
        self.case_ids.remove(case_id)
        return True

    def clear(self):
        if self.error:
            raise self.error
        deleted_count = len(self.case_ids)
        self.case_ids.clear()
        return deleted_count

    def entity_graph(self, minimum_case_count=2, case_limit=100, max_edges=1_000):
        if self.error:
            raise self.error
        self.graph_calls.append((minimum_case_count, case_limit, max_edges))
        return self.graph_result


class _OcrService:
    def __init__(self, error=None, max_bytes=5 * 1024 * 1024):
        self.error = error
        self.policy = SimpleNamespace(max_bytes=max_bytes)
        self.calls = []

    def extract(self, image_bytes, media_type):
        self.calls.append((image_bytes, media_type))
        if self.error is not None:
            raise self.error
        return OcrResult(
            text="Urgent KYC verification required",
            engine="test-ocr",
            languages="eng+hin",
            width=640,
            height=480,
        )


def _settings(store_cases_by_default=False, allowed_hosts=(), demo_api_key=None):
    return Settings(
        model_backend="tfidf",
        database_path=None,
        hmac_secret="test-secret",
        retention_days=30,
        store_cases_by_default=store_cases_by_default,
        environment="test",
        allowed_hosts=allowed_hosts,
        demo_api_key=demo_api_key,
    )


def _graph_result():
    entity_id = "phone_" + "a" * 64
    return build_entity_graph(
        [
            EntityLink(
                case_id="case-one",
                created_at="2026-08-08T12:00:00Z",
                predicted_label="kyc_scam",
                risk_level="high",
                risk_score=91.0,
                entity_type="phone",
                entity_id=entity_id,
                masked_value="******1234",
            ),
            EntityLink(
                case_id="case-two",
                created_at="2026-08-08T12:05:00Z",
                predicted_label="kyc_scam",
                risk_level="medium",
                risk_score=72.0,
                entity_type="phone",
                entity_id=entity_id,
                masked_value="******1234",
            ),
        ]
    )


def _client(
    store_cases_by_default=False,
    store=None,
    allowed_hosts=(),
    ocr_service=None,
    demo_api_key=None,
):
    app = api.create_app(
        settings=_settings(store_cases_by_default, allowed_hosts, demo_api_key),
        predictor=_StubPredictor(Prediction("kyc_scam", 0.91, "test", "test-v1", False)),
        store=store or _Store(),
        ocr_service=ocr_service,
    )
    return app, TestClient(app)


def test_health_endpoint():
    app, test_client = _client()
    with test_client:
        response = test_client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"
        assert app.state.analysis_service is not None


def test_hosted_demo_key_protects_data_routes_but_not_health_or_readiness():
    demo_key = "d7Nw5vR2_yQ8mK4pL9sX1cF6hJ3uT0zB7eG5aI"
    _, test_client = _client(demo_api_key=demo_key)

    with test_client:
        assert test_client.get("/health").status_code == 200
        assert test_client.get("/ready").status_code == 200
        assert test_client.post(
            "/analyze", json={"text": "Urgent fake KYC update"}
        ).status_code == 401
        assert test_client.post(
            "/analyze",
            headers={"X-FraudLens-Demo-Key": "wrong-key"},
            json={"text": "Urgent fake KYC update"},
        ).status_code == 401

        response = test_client.post(
            "/analyze",
            headers={"X-FraudLens-Demo-Key": demo_key},
            json={"text": "Urgent fake KYC update"},
        )

    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-store"


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


def test_analyze_endpoint_rejects_oversized_chunked_json_before_parsing():
    _, test_client = _client()
    chunks = iter([b'{"text":"', b"x" * (64 * 1024), b'"}'])

    with test_client:
        response = test_client.post(
            "/analyze",
            content=chunks,
            headers={"content-type": "application/json"},
        )

    assert response.status_code == 413
    assert response.json() == {"detail": "Request body is too large"}


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


@pytest.mark.parametrize("media_type", ["image/png", "image/jpeg"])
def test_analyze_image_accepts_raw_png_and_jpeg_requests(media_type):
    ocr_service = _OcrService()
    _, test_client = _client(ocr_service=ocr_service)

    with test_client:
        response = test_client.post(
            "/analyze-image",
            content=b"raw-image-payload",
            headers={"content-type": media_type},
            params={"user_notes": "customer supplied screenshot", "store_case": "false"},
        )

    assert response.status_code == 200
    assert ocr_service.calls == [(b"raw-image-payload", media_type)]
    assert response.json()["metadata"]["input_source"] == "image"
    assert response.json()["metadata"]["ocr_engine"] == "test-ocr"
    assert response.json()["metadata"]["source_image_retained"] is False


def test_analyze_image_uses_the_runtime_storage_default_when_query_is_omitted():
    store = _Store()
    _, test_client = _client(
        store_cases_by_default=True,
        store=store,
        ocr_service=_OcrService(),
    )

    with test_client:
        response = test_client.post(
            "/analyze-image",
            content=b"raw-image-payload",
            headers={"content-type": "image/png"},
        )

    assert response.status_code == 200
    assert response.json()["metadata"]["stored"] is True
    assert len(store.saved) == 1


def test_analyze_image_rejects_oversized_content_length_before_ocr():
    ocr_service = _OcrService(max_bytes=4)
    _, test_client = _client(ocr_service=ocr_service)

    with test_client:
        response = test_client.post(
            "/analyze-image",
            content=b"x",
            headers={"content-type": "image/png", "content-length": "5"},
        )

    assert response.status_code == 413
    assert response.json() == {"detail": "Image upload is too large"}
    assert ocr_service.calls == []


def test_analyze_image_stops_when_an_unknown_length_stream_exceeds_the_limit():
    ocr_service = _OcrService(max_bytes=4)
    _, test_client = _client(ocr_service=ocr_service)

    with test_client:
        response = test_client.post(
            "/analyze-image",
            content=iter([b"12", b"345"]),
            headers={"content-type": "image/png"},
        )

    assert response.status_code == 413
    assert response.json() == {"detail": "Image upload is too large"}
    assert ocr_service.calls == []


def test_limited_image_stream_retains_only_max_plus_one_and_stops_iteration():
    requested_slices = []
    requested_next_chunk = False

    class _TrackingChunk(bytes):
        def __getitem__(self, key):
            if isinstance(key, slice):
                requested_slices.append(key)
            return super().__getitem__(key)

    async def producer():
        nonlocal requested_next_chunk
        yield _TrackingChunk(b"123456789")
        requested_next_chunk = True
        raise AssertionError("stream iteration continued after the size limit")

    with pytest.raises(ImageTooLargeError):
        asyncio.run(api._read_limited_image_stream(producer(), max_bytes=4))

    assert requested_slices == [slice(None, 5, None)]
    assert requested_next_chunk is False


@pytest.mark.parametrize(
    ("headers", "expected_detail"),
    [
        ({}, "Unsupported image media type"),
        ({"content-type": "application/octet-stream"}, "Unsupported image media type"),
        (
            {"content-type": "image/png", "content-encoding": "gzip"},
            "Unsupported content encoding",
        ),
    ],
)
def test_analyze_image_rejects_unsupported_media_and_encoding(headers, expected_detail):
    ocr_service = _OcrService()
    _, test_client = _client(ocr_service=ocr_service)

    with test_client:
        response = test_client.post("/analyze-image", content=b"image", headers=headers)

    assert response.status_code == 415
    assert response.json() == {"detail": expected_detail}
    assert ocr_service.calls == []


@pytest.mark.parametrize("content_length", ["not-a-number", "-1", "+1", "1.0"])
def test_analyze_image_rejects_malformed_content_length(content_length):
    ocr_service = _OcrService()
    _, test_client = _client(ocr_service=ocr_service)

    with test_client:
        response = test_client.post(
            "/analyze-image",
            content=b"image",
            headers={"content-type": "image/png", "content-length": content_length},
        )

    assert response.status_code == 400
    assert response.json() == {"detail": "Invalid Content-Length"}
    assert ocr_service.calls == []


@pytest.mark.parametrize(
    "error",
    [
        InvalidImageError("private invalid image details"),
        NoTextDetectedError("private no-text details"),
        OcrError("private bounded OCR text details"),
    ],
)
def test_analyze_image_maps_invalid_or_unusable_images_to_generic_422(error):
    _, test_client = _client(ocr_service=_OcrService(error=error))

    with test_client:
        response = test_client.post(
            "/analyze-image",
            content=b"image",
            headers={"content-type": "image/png"},
        )

    assert response.status_code == 422
    assert response.json() == {"detail": "Image could not be analyzed"}
    assert "private" not in response.text


@pytest.mark.parametrize(
    ("error", "status_code", "detail"),
    [
        (OcrUnavailableError("/private/tesseract missing"), 503, "OCR service unavailable"),
        (OcrTimeoutError("private timeout details"), 504, "OCR service timed out"),
        (RuntimeError("private implementation details"), 500, "Internal server error"),
    ],
)
def test_analyze_image_maps_operational_failures_without_leaking_details(
    error, status_code, detail
):
    _, test_client = _client(ocr_service=_OcrService(error=error))

    with test_client:
        response = test_client.post(
            "/analyze-image",
            content=b"image",
            headers={"content-type": "image/png"},
        )

    assert response.status_code == status_code
    assert response.json() == {"detail": detail}
    assert "private" not in response.text


def test_analyze_image_dispatches_workflow_to_threadpool_and_preserves_error_mapping(
    monkeypatch,
):
    dispatched = []

    async def recording_threadpool(function, *args, **kwargs):
        dispatched.append((function, args, kwargs))
        return function(*args, **kwargs)

    monkeypatch.setattr(api, "run_in_threadpool", recording_threadpool)
    application, test_client = _client(
        ocr_service=_OcrService(error=OcrTimeoutError("private timeout details"))
    )

    with test_client:
        response = test_client.post(
            "/analyze-image",
            content=b"image",
            headers={"content-type": "image/png"},
        )

    assert response.status_code == 504
    assert response.json() == {"detail": "OCR service timed out"}
    assert len(dispatched) == 1
    function, args, kwargs = dispatched[0]
    assert function.__self__ is application.state.image_analysis_service
    assert function.__name__ == "analyze"
    assert args[0].image_bytes == b"image"
    assert kwargs == {}


def test_cases_limit_and_security_headers_are_constrained():
    _, test_client = _client()
    with test_client:
        for limit in (0, 101):
            assert test_client.get("/cases", params={"limit": limit}).status_code == 422
        response = test_client.get("/health")

    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["cache-control"] == "no-store"


def test_graph_endpoint_returns_a_serializable_graph_for_default_and_bounded_queries():
    store = _Store()
    _, test_client = _client(store=store)

    with test_client:
        default_response = test_client.get("/graph")
        bounded_response = test_client.get(
            "/graph", params={"minimum_case_count": 4, "case_limit": 20}
        )

    assert default_response.status_code == 200
    assert bounded_response.status_code == 200
    payload = default_response.json()
    assert payload["case_nodes"]
    assert payload["entity_nodes"]
    assert payload["edges"]
    assert payload["components"]
    assert payload["summary"] == {
        "case_count": 2,
        "entity_count": 1,
        "edge_count": 2,
        "component_count": 1,
        "truncated": False,
    }
    assert store.graph_calls == [(2, 100, 1_000), (4, 20, 1_000)]
    assert default_response.headers["x-content-type-options"] == "nosniff"
    assert default_response.headers["cache-control"] == "no-store"


@pytest.mark.parametrize(
    "params",
    [
        {"minimum_case_count": 1},
        {"minimum_case_count": 21},
        {"case_limit": 0},
        {"case_limit": 101},
    ],
)
def test_graph_endpoint_rejects_unbounded_queries_before_reading_storage(params):
    store = _Store()
    _, test_client = _client(store=store)

    with test_client:
        response = test_client.get("/graph", params=params)

    assert response.status_code == 422
    assert store.graph_calls == []


def test_graph_endpoint_hides_storage_failure_details():
    _, test_client = _client(store=_Store(error=RuntimeError("/private/cases.sqlite SQL secret")))

    with test_client:
        response = test_client.get("/graph")

    assert response.status_code == 500
    assert response.json() == {"detail": "Internal server error"}
    assert "/private" not in response.text
    assert "SQL" not in response.text
    assert "secret" not in response.text


def test_graph_endpoint_returns_a_valid_zero_summary_for_an_empty_graph():
    store = _Store()
    store.graph_result = build_entity_graph(())
    _, test_client = _client(store=store)

    with test_client:
        response = test_client.get("/graph")

    assert response.status_code == 200
    assert response.json() == {
        "case_nodes": [],
        "entity_nodes": [],
        "edges": [],
        "components": [],
        "summary": {
            "case_count": 0,
            "entity_count": 0,
            "edge_count": 0,
            "component_count": 0,
            "truncated": False,
        },
    }


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


def test_analyze_post_purges_an_expired_raw_case_during_the_save_transaction(tmp_path):
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
        with sqlite3.connect(configured_path) as conn:
            conn.execute(
                """
                INSERT INTO cases
                (case_id, created_at, original_text, predicted_label, confidence, risk_level, risk_score,
                 result_json, stored_raw_text, expires_at, model_version)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    "expired-raw",
                    "2000-01-01T00:00:00+00:00",
                    "expired raw text",
                    "kyc_scam",
                    0.8,
                    "high",
                    70,
                    "{}",
                    1,
                    "2000-01-31T00:00:00+00:00",
                    "legacy",
                ),
            )

        response = test_client.post("/analyze", json={"text": "urgent verification"})

    with sqlite3.connect(configured_path) as conn:
        remaining_ids = [row[0] for row in conn.execute("SELECT case_id FROM cases")]
    assert response.status_code == 200
    assert remaining_ids == [response.json()["case_id"]]


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
        model_backend="unsupported",
        database_path=Path(tmp_path) / "cases.sqlite3",
        hmac_secret="test-secret",
        retention_days=30,
        store_cases_by_default=False,
        environment="test",
        allowed_hosts=(),
    )

    with pytest.raises(ValueError, match="Application configuration is invalid"):
        api.create_app(settings=settings, predictor_registry=PredictorRegistry({}))


def test_delete_case_returns_success_once_then_not_found():
    store = _Store(case_ids=("case-1",))
    _, test_client = _client(store=store)

    with test_client:
        refused = test_client.delete("/cases/case-1")
        deleted = test_client.delete("/cases/case-1", params={"confirm": "true"})
        missing = test_client.delete("/cases/case-1", params={"confirm": "true"})

    assert refused.status_code == 400
    assert refused.json() == {"detail": "Explicit confirmation is required"}
    assert deleted.status_code == 200
    assert deleted.json() == {"deleted": True, "case_id": "case-1"}
    assert missing.status_code == 404
    assert missing.json() == {"detail": "Case not found"}


def test_clear_case_history_requires_explicit_confirmation():
    store = _Store(case_ids=("case-1", "case-2"))
    _, test_client = _client(store=store)

    with test_client:
        omitted = test_client.delete("/cases")
        refused = test_client.delete("/cases", params={"confirm": "false"})
        cleared = test_client.delete("/cases", params={"confirm": "true"})

    assert omitted.status_code == 400
    assert refused.status_code == 400
    assert omitted.json() == {"detail": "Explicit confirmation is required"}
    assert cleared.status_code == 200
    assert cleared.json() == {"deleted_count": 2}


def test_delete_endpoints_hide_storage_error_details():
    store = _Store(error=RuntimeError("/private/cases.sqlite3 failed"), case_ids=("case-1",))
    _, test_client = _client(store=store)

    with test_client:
        one = test_client.delete("/cases/case-1", params={"confirm": "true"})
        all_cases = test_client.delete("/cases", params={"confirm": "true"})

    assert one.status_code == 500
    assert all_cases.status_code == 500
    assert one.json() == {"detail": "Internal server error"}
    assert "/private" not in one.text + all_cases.text
