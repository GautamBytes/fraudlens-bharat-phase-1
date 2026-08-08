from pathlib import Path
from types import SimpleNamespace

from fastapi.testclient import TestClient

from fraudlens.api import create_app
from fraudlens.ocr import OcrResult
from fraudlens.prediction import Prediction
from fraudlens.settings import Settings


class _ReleasePredictor:
    def predict(self, text):
        return Prediction("kyc_scam", 0.91, "acceptance", "acceptance-v1", False)


class _ReleaseOcr:
    policy = SimpleNamespace(max_bytes=5 * 1024 * 1024)

    def extract(self, image_bytes, media_type):
        assert image_bytes == b"raw-image-payload"
        assert media_type == "image/png"
        return OcrResult(
            text="Urgent KYC caller 9876543210 asked to verify now",
            engine="acceptance-ocr",
            languages="eng+hin",
            width=800,
            height=600,
        )


def _release_app(database_path: Path):
    return create_app(
        settings=Settings(
            model_backend="tfidf",
            database_path=database_path,
            hmac_secret="release-acceptance-secret",
            retention_days=30,
            store_cases_by_default=False,
            environment="test",
            allowed_hosts=(),
        ),
        predictor=_ReleasePredictor(),
        ocr_service=_ReleaseOcr(),
    )


def test_complete_release_journey_preserves_consent_and_privacy(tmp_path):
    database_path = tmp_path / "release.sqlite3"
    application = _release_app(database_path)

    with TestClient(application) as client:
        assert client.get("/ready").status_code == 200

        unconsented = client.post(
            "/analyze",
            json={"text": "Urgent verification request without storage consent"},
        )
        assert unconsented.status_code == 200
        assert unconsented.json()["metadata"]["stored"] is False
        assert client.get("/cases").json() == []

        text_result = client.post(
            "/analyze",
            json={
                "text": "Call 9876543210 for urgent KYC verification now",
                "user_notes": "Release acceptance note",
                "store_case": True,
            },
        )
        image_result = client.post(
            "/analyze-image",
            params={"store_case": "true"},
            content=b"raw-image-payload",
            headers={"content-type": "image/png"},
        )

        assert text_result.status_code == 200
        assert image_result.status_code == 200
        assert text_result.json()["metadata"]["stored"] is True
        assert image_result.json()["metadata"] == {
            "input_source": "image",
            "ocr_engine": "acceptance-ocr",
            "ocr_languages": "eng+hin",
            "ocr_width": 800,
            "ocr_height": 600,
            "source_image_retained": False,
            "prediction_source": "acceptance",
            "prediction_model_version": "acceptance-v1",
            "prediction_abstained": False,
            "user_notes": None,
            "stored": True,
        }

        text_case_id = text_result.json()["case_id"]
        image_case_id = image_result.json()["case_id"]
        listed = client.get("/cases").json()
        assert {case["case_id"] for case in listed} == {text_case_id, image_case_id}
        assert client.get("/cases/{}".format(text_case_id)).status_code == 200

        graph = client.get("/graph")
        assert graph.status_code == 200
        assert graph.json()["summary"] == {
            "case_count": 2,
            "entity_count": 1,
            "edge_count": 2,
            "component_count": 1,
            "truncated": False,
        }
        assert graph.json()["entity_nodes"][0]["entity_type"] == "phone"
        assert graph.json()["entity_nodes"][0]["masked_value"] == "******3210"
        assert "9876543210" not in graph.text

        deleted = client.delete(
            "/cases/{}".format(text_case_id), params={"confirm": "true"}
        )
        assert deleted.status_code == 200
        assert client.get("/cases/{}".format(text_case_id)).status_code == 404
        assert client.get("/graph").json()["summary"]["edge_count"] == 0

        cleared = client.delete("/cases", params={"confirm": "true"})
        assert cleared.json() == {"deleted_count": 1}
        assert client.get("/cases").json() == []

    assert b"raw-image-payload" not in database_path.read_bytes()
