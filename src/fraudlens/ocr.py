"""Safe, in-memory OCR preparation for uploaded screenshots."""

from __future__ import annotations

import io
import subprocess
import warnings
from dataclasses import dataclass
from typing import Callable

from PIL import Image, ImageOps, UnidentifiedImageError


@dataclass(frozen=True)
class ImagePolicy:
    max_bytes: int = 5 * 1024 * 1024
    max_width: int = 4096
    max_height: int = 4096
    max_pixels: int = 16_000_000
    max_text_chars: int = 20_000
    timeout_seconds: int = 15


class OcrError(RuntimeError):
    """Base class for OCR processing errors."""


class InvalidImageError(OcrError):
    """The upload is not a supported, valid image."""


class ImageTooLargeError(OcrError):
    """The upload exceeds an encoded or decoded image limit."""


class NoTextDetectedError(OcrError):
    """OCR completed but did not find usable text."""


class OcrUnavailableError(OcrError):
    """The configured local OCR engine is unavailable."""


class OcrTimeoutError(OcrError):
    """The OCR engine did not complete within the configured timeout."""


@dataclass(frozen=True)
class OcrResult:
    text: str
    engine: str
    languages: str
    width: int
    height: int


class TesseractOcrEngine:
    """Small shell-free adapter around the local tesseract executable."""

    engine_name = "tesseract"

    def __init__(
        self,
        executable: str = "tesseract",
        languages: str = "eng+hin",
        runner: Callable[..., subprocess.CompletedProcess[bytes]] = subprocess.run,
    ) -> None:
        self.executable = executable
        self.languages = languages
        self._runner = runner

    def extract_text(self, normalized_png: bytes, timeout_seconds: int) -> str:
        command = [
            self.executable,
            "stdin",
            "stdout",
            "-l",
            self.languages,
            "--psm",
            "6",
        ]
        try:
            completed = self._runner(
                command,
                input=normalized_png,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=timeout_seconds,
                check=False,
                shell=False,
            )
        except FileNotFoundError as exc:
            raise OcrUnavailableError("Tesseract executable is unavailable") from exc
        except subprocess.TimeoutExpired as exc:
            raise OcrTimeoutError("OCR timed out") from exc
        except OSError as exc:
            raise OcrUnavailableError("Tesseract could not be started") from exc

        if completed.returncode != 0:
            raise OcrUnavailableError("Tesseract failed")

        try:
            return completed.stdout.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise OcrError("Tesseract returned invalid text") from exc


class OcrService:
    """Validates screenshots and invokes OCR without writing uploads to disk."""

    _MIME_BY_FORMAT = {
        "PNG": "image/png",
        "JPEG": "image/jpeg",
    }

    def __init__(
        self,
        engine: TesseractOcrEngine | object | None = None,
        policy: ImagePolicy | None = None,
    ) -> None:
        self.engine = engine if engine is not None else TesseractOcrEngine()
        self.policy = policy if policy is not None else ImagePolicy()

    def extract(self, image_bytes: bytes, media_type: str) -> OcrResult:
        normalized_png, width, height = self._normalize(image_bytes, media_type)
        text = self.engine.extract_text(normalized_png, self.policy.timeout_seconds)
        if not isinstance(text, str):
            raise OcrError("OCR engine returned invalid text")
        if not text.strip():
            raise NoTextDetectedError("No text detected in image")
        if len(text) > self.policy.max_text_chars:
            raise OcrError("OCR text exceeds the configured limit")

        return OcrResult(
            text=text,
            engine=getattr(self.engine, "engine_name", "tesseract"),
            languages=getattr(self.engine, "languages", "eng"),
            width=width,
            height=height,
        )

    def _normalize(self, image_bytes: bytes, media_type: str) -> tuple[bytes, int, int]:
        if not isinstance(image_bytes, bytes) or not image_bytes:
            raise InvalidImageError("Image upload is empty or invalid")
        if len(image_bytes) > self.policy.max_bytes:
            raise ImageTooLargeError("Image encoded size exceeds the configured limit")
        if not isinstance(media_type, str):
            raise InvalidImageError("Image media type is invalid")

        supplied_mime = media_type.split(";", 1)[0].strip().lower()
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("error", Image.DecompressionBombWarning)
                with Image.open(io.BytesIO(image_bytes)) as image:
                    image_format = image.format
                    if getattr(image, "n_frames", 1) != 1:
                        raise InvalidImageError("multi-frame images are not supported")
                    expected_mime = self._MIME_BY_FORMAT.get(image_format or "")
                    if expected_mime is None:
                        raise InvalidImageError("Unsupported image format")
                    if supplied_mime != expected_mime:
                        raise InvalidImageError(
                            "Image media type does not match its encoded format"
                        )

                    width, height = image.size
                    if (
                        width > self.policy.max_width
                        or height > self.policy.max_height
                        or width * height > self.policy.max_pixels
                    ):
                        raise ImageTooLargeError(
                            "Image dimensions exceed the configured limit"
                        )

                    image.load()
                    transposed = ImageOps.exif_transpose(image).convert("RGB")
                    rgb_image = Image.new("RGB", transposed.size)
                    rgb_image.paste(transposed)
                    width, height = rgb_image.size
                    output = io.BytesIO()
                    rgb_image.save(output, format="PNG")
                    return output.getvalue(), width, height
        except Image.DecompressionBombWarning as exc:
            raise ImageTooLargeError("Image triggered decompression bomb protection") from exc
        except Image.DecompressionBombError as exc:
            raise ImageTooLargeError("Image triggered decompression bomb protection") from exc
        except InvalidImageError:
            raise
        except (UnidentifiedImageError, OSError, SyntaxError, ValueError) as exc:
            raise InvalidImageError("Image is corrupt or invalid") from exc
