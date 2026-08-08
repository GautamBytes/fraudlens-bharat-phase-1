"""OCR-backed analysis workflow for raw screenshot uploads."""

from dataclasses import dataclass
from typing import Optional

from fraudlens.analysis_service import AnalysisInput, AnalysisService
from fraudlens.ocr import OcrService
from fraudlens.schemas import AnalysisResult


@dataclass(frozen=True)
class ImageAnalysisInput:
    image_bytes: bytes
    media_type: str
    user_notes: Optional[str] = None
    store_case: bool = False


class ImageAnalysisService:
    """Extract screenshot text and delegate fraud analysis without retaining pixels."""

    def __init__(self, ocr_service: OcrService, analysis_service: AnalysisService) -> None:
        self._ocr_service = ocr_service
        self._analysis_service = analysis_service

    def analyze(self, analysis_input: ImageAnalysisInput) -> AnalysisResult:
        ocr_result = self._ocr_service.extract(
            analysis_input.image_bytes,
            analysis_input.media_type,
        )
        return self._analysis_service.analyze(
            AnalysisInput(
                text=ocr_result.text,
                user_notes=analysis_input.user_notes,
                store_case=analysis_input.store_case,
                metadata={
                    "input_source": "image",
                    "ocr_engine": ocr_result.engine,
                    "ocr_languages": ocr_result.languages,
                    "ocr_width": ocr_result.width,
                    "ocr_height": ocr_result.height,
                    "source_image_retained": False,
                },
            )
        )
