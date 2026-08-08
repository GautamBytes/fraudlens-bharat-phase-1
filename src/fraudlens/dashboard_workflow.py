"""Pure screenshot-upload workflow for the Streamlit dashboard."""

from dataclasses import dataclass

from fraudlens.image_analysis import ImageAnalysisInput, ImageAnalysisService
from fraudlens.ocr import (
    ImageTooLargeError,
    ImagePolicy,
    InvalidImageError,
    NoTextDetectedError,
    OcrError,
    OcrTimeoutError,
    OcrUnavailableError,
)
from fraudlens.schemas import AnalysisResult


@dataclass(frozen=True)
class ScreenshotAnalysisOutcome:
    result: AnalysisResult | None = None
    error_message: str | None = None


def analyze_uploaded_file(
    image_analysis_service: ImageAnalysisService,
    *,
    uploaded_file,
    store_case: bool,
) -> ScreenshotAnalysisOutcome:
    """Reject an oversize Streamlit upload before materializing its bytes."""
    if uploaded_file.size > ImagePolicy().max_bytes:
        return ScreenshotAnalysisOutcome(
            error_message="This screenshot exceeds the supported size limit."
        )
    return analyze_uploaded_screenshot(
        image_analysis_service,
        image_bytes=uploaded_file.getvalue(),
        media_type=uploaded_file.type,
        store_case=store_case,
    )


def analyze_uploaded_screenshot(
    image_analysis_service: ImageAnalysisService,
    *,
    image_bytes: bytes,
    media_type: str,
    store_case: bool,
) -> ScreenshotAnalysisOutcome:
    """Analyze one screenshot and convert OCR failures to safe UI copy."""
    try:
        result = image_analysis_service.analyze(
            ImageAnalysisInput(
                image_bytes=image_bytes,
                media_type=media_type,
                store_case=store_case,
            )
        )
    except OcrError as error:
        return ScreenshotAnalysisOutcome(error_message=_safe_ocr_error_message(error))
    return ScreenshotAnalysisOutcome(result=result)


def _safe_ocr_error_message(error: OcrError) -> str:
    if isinstance(error, InvalidImageError):
        return "Upload a valid PNG or JPEG screenshot."
    if isinstance(error, ImageTooLargeError):
        return "This screenshot exceeds the supported size limit."
    if isinstance(error, NoTextDetectedError):
        return "No readable text was found in this screenshot."
    if isinstance(error, OcrUnavailableError):
        return "Screenshot analysis is temporarily unavailable. Please try again later."
    if isinstance(error, OcrTimeoutError):
        return "Screenshot analysis timed out. Please try again."
    return "We couldn't read text from this screenshot. Please try another image."
