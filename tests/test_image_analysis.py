from dataclasses import FrozenInstanceError
from datetime import datetime

import pytest

from fraudlens.analysis_service import AnalysisService
from fraudlens.image_analysis import ImageAnalysisInput, ImageAnalysisService
from fraudlens.ocr import OcrResult
from fraudlens.prediction import Prediction


class _StubPredictor:
    def predict(self, text):
        assert text == "urgent kyc verification required"
        return Prediction("kyc_scam", 0.91, "test", "test-v1", False)


class _RecordingStore:
    def __init__(self):
        self.saved = []

    def save(self, result):
        self.saved.append(result)


class _RecordingOcrService:
    def __init__(self):
        self.calls = []

    def extract(self, image_bytes, media_type):
        self.calls.append((image_bytes, media_type))
        return OcrResult(
            text="Urgent KYC verification required",
            engine="tesseract",
            languages="eng+hin",
            width=1080,
            height=1920,
        )


def _service(store=None):
    analysis_service = AnalysisService(
        predictor=_StubPredictor(),
        store=store,
        clock=lambda: datetime(2026, 8, 8, 12, 0, 0),
        id_generator=lambda: "case-image-123",
    )
    ocr_service = _RecordingOcrService()
    return ImageAnalysisService(ocr_service, analysis_service), ocr_service


def test_image_analysis_input_is_immutable():
    analysis_input = ImageAnalysisInput(b"image", "image/png")

    with pytest.raises(FrozenInstanceError):
        analysis_input.store_case = True


def test_image_workflow_propagates_only_bounded_ocr_metadata_without_storing_by_default():
    store = _RecordingStore()
    service, ocr_service = _service(store)

    result = service.analyze(
        ImageAnalysisInput(
            image_bytes=b"private-image-payload",
            media_type="image/png",
            user_notes="reported by customer",
        )
    )

    assert ocr_service.calls == [(b"private-image-payload", "image/png")]
    assert result.original_text == "Urgent KYC verification required"
    assert result.metadata == {
        "input_source": "image",
        "ocr_engine": "tesseract",
        "ocr_languages": "eng+hin",
        "ocr_width": 1080,
        "ocr_height": 1920,
        "source_image_retained": False,
        "prediction_source": "test",
        "prediction_model_version": "test-v1",
        "prediction_abstained": False,
        "user_notes": "reported by customer",
        "stored": False,
    }
    assert store.saved == []


def test_image_workflow_persists_analysis_only_with_explicit_consent():
    store = _RecordingStore()
    service, _ = _service(store)

    result = service.analyze(
        ImageAnalysisInput(
            image_bytes=b"private-image-payload",
            media_type="image/jpeg",
            store_case=True,
        )
    )

    assert result.metadata["stored"] is True
    assert store.saved == [result]


def test_image_workflow_never_returns_or_stores_image_artifacts():
    store = _RecordingStore()
    service, _ = _service(store)

    result = service.analyze(
        ImageAnalysisInput(
            image_bytes=b"UNIQUE-RAW-IMAGE-BYTES",
            media_type="image/png",
            store_case=True,
        )
    )

    public_result = repr(result.model_dump(mode="json"))
    persisted_result = repr(store.saved[0].model_dump(mode="json"))
    for serialized in (public_result, persisted_result):
        assert "UNIQUE-RAW-IMAGE-BYTES" not in serialized
        assert "normalized_png" not in serialized
        assert "filename" not in serialized
        assert "sha256" not in serialized
        assert "base64" not in serialized
        assert "subprocess" not in serialized
