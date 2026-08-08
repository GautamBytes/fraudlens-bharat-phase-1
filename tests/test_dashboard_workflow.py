import pytest

from fraudlens.ocr import (
    ImageTooLargeError,
    InvalidImageError,
    NoTextDetectedError,
    OcrError,
    OcrTimeoutError,
    OcrUnavailableError,
)


class _ImageAnalysisService:
    def __init__(self, result=None, error=None):
        self.result = result
        self.error = error
        self.calls = []

    def analyze(self, analysis_input):
        self.calls.append(analysis_input)
        if self.error is not None:
            raise self.error
        return self.result


class _OversizeUpload:
    type = "image/png"

    def __init__(self, size):
        self.size = size
        self.getvalue_calls = 0

    def getvalue(self):
        self.getvalue_calls += 1
        raise AssertionError("oversize upload bytes must not be materialized")


def test_analyze_uploaded_file_rejects_oversize_upload_before_materializing_bytes():
    from fraudlens.dashboard_workflow import analyze_uploaded_file
    from fraudlens.ocr import ImagePolicy

    uploaded_file = _OversizeUpload(ImagePolicy().max_bytes + 1)
    service = _ImageAnalysisService()

    outcome = analyze_uploaded_file(service, uploaded_file=uploaded_file, store_case=False)

    assert outcome.result is None
    assert outcome.error_message == "This screenshot exceeds the supported size limit."
    assert uploaded_file.getvalue_calls == 0
    assert service.calls == []


def test_analyze_uploaded_screenshot_builds_an_image_analysis_input():
    from fraudlens.dashboard_workflow import analyze_uploaded_screenshot

    result = object()
    service = _ImageAnalysisService(result=result)

    outcome = analyze_uploaded_screenshot(
        service,
        image_bytes=b"screenshot",
        media_type="image/png",
        store_case=True,
    )

    assert outcome.result is result
    assert outcome.error_message is None
    assert len(service.calls) == 1
    assert service.calls[0].image_bytes == b"screenshot"
    assert service.calls[0].media_type == "image/png"
    assert service.calls[0].store_case is True


@pytest.mark.parametrize(
    ("error", "expected_message"),
    [
        (InvalidImageError("/private/bad.png"), "Upload a valid PNG or JPEG screenshot."),
        (ImageTooLargeError("size=999999"), "This screenshot exceeds the supported size limit."),
        (NoTextDetectedError("private OCR output"), "No readable text was found in this screenshot."),
        (OcrUnavailableError("stderr private"), "Screenshot analysis is temporarily unavailable. Please try again later."),
        (OcrTimeoutError("/tmp/ocr timeout"), "Screenshot analysis timed out. Please try again."),
        (OcrError("raw engine error"), "We couldn't read text from this screenshot. Please try another image."),
    ],
)
def test_analyze_uploaded_screenshot_returns_safe_fixed_ocr_error_messages(
    error, expected_message
):
    from fraudlens.dashboard_workflow import analyze_uploaded_screenshot

    outcome = analyze_uploaded_screenshot(
        _ImageAnalysisService(error=error),
        image_bytes=b"screenshot",
        media_type="image/png",
        store_case=False,
    )

    assert outcome.result is None
    assert outcome.error_message == expected_message
    assert str(error) not in outcome.error_message
