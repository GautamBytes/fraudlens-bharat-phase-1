from __future__ import annotations

import io
import subprocess

import pytest
from PIL import Image, PngImagePlugin

from fraudlens.ocr import (
    ImagePolicy,
    ImageTooLargeError,
    InvalidImageError,
    NoTextDetectedError,
    OcrError,
    OcrService,
    OcrTimeoutError,
    OcrUnavailableError,
    TesseractOcrEngine,
)


def image_bytes(
    image_format: str = "PNG",
    *,
    size: tuple[int, int] = (3, 2),
    mode: str = "RGB",
    pnginfo: PngImagePlugin.PngInfo | None = None,
    icc_profile: bytes | None = None,
) -> bytes:
    image = Image.new(mode, size, "white")
    output = io.BytesIO()
    image.save(
        output,
        image_format,
        pnginfo=pnginfo,
        **({"icc_profile": icc_profile} if icc_profile is not None else {}),
    )
    return output.getvalue()


class RecordingEngine:
    languages = "eng+hin"
    engine_name = "recording"

    def __init__(self, text: str = "UPI payment") -> None:
        self.text = text
        self.normalized_png: bytes | None = None
        self.timeout_seconds: int | None = None

    def extract_text(self, normalized_png: bytes, timeout_seconds: int) -> str:
        self.normalized_png = normalized_png
        self.timeout_seconds = timeout_seconds
        return self.text


def test_rejects_mime_and_image_format_mismatch() -> None:
    service = OcrService(engine=RecordingEngine())
    with pytest.raises(InvalidImageError, match="does not match"):
        service.extract(image_bytes("JPEG"), "image/png")


def test_rejects_valid_webp_images() -> None:
    service = OcrService(engine=RecordingEngine())
    with pytest.raises(InvalidImageError, match="Unsupported"):
        service.extract(image_bytes("WEBP"), "image/webp")


def test_rejects_encoded_images_over_the_byte_limit() -> None:
    service = OcrService(engine=RecordingEngine(), policy=ImagePolicy(max_bytes=10))
    with pytest.raises(ImageTooLargeError, match="encoded size"):
        service.extract(image_bytes(), "image/png")


@pytest.mark.parametrize(
    ("size", "policy"),
    [
        ((5, 2), ImagePolicy(max_width=4)),
        ((2, 5), ImagePolicy(max_height=4)),
        ((3, 3), ImagePolicy(max_pixels=8)),
    ],
)
def test_rejects_images_over_dimension_or_pixel_limits(
    size: tuple[int, int], policy: ImagePolicy
) -> None:
    service = OcrService(engine=RecordingEngine(), policy=policy)
    with pytest.raises(ImageTooLargeError):
        service.extract(image_bytes(size=size), "image/png")


def test_rejects_multi_frame_images() -> None:
    first = Image.new("RGB", (2, 2), "white")
    second = Image.new("RGB", (2, 2), "black")
    output = io.BytesIO()
    first.save(output, "GIF", save_all=True, append_images=[second])
    service = OcrService(engine=RecordingEngine())
    with pytest.raises(InvalidImageError, match="multi-frame"):
        service.extract(output.getvalue(), "image/gif")


@pytest.mark.parametrize("payload", [b"not an image", image_bytes()[:40]])
def test_rejects_corrupt_or_truncated_images(payload: bytes) -> None:
    service = OcrService(engine=RecordingEngine())
    with pytest.raises(InvalidImageError):
        service.extract(payload, "image/png")


def test_converts_pillow_decompression_bomb_warnings_to_domain_errors(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(Image, "MAX_IMAGE_PIXELS", 1)
    service = OcrService(engine=RecordingEngine())
    with pytest.raises(ImageTooLargeError, match="decompression bomb"):
        service.extract(image_bytes(size=(2, 2)), "image/png")


def test_normalizes_to_metadata_free_rgb_png_before_ocr() -> None:
    metadata = PngImagePlugin.PngInfo()
    metadata.add_text("secret", "remove me")
    engine = RecordingEngine()
    service = OcrService(engine=engine)

    result = service.extract(
        image_bytes(mode="RGBA", pnginfo=metadata, icc_profile=b"private-profile"),
        "image/png; charset=binary",
    )

    assert result.text == "UPI payment"
    assert result.engine == "recording"
    assert result.languages == "eng+hin"
    assert (result.width, result.height) == (3, 2)
    assert engine.timeout_seconds == 15
    assert engine.normalized_png is not None
    with Image.open(io.BytesIO(engine.normalized_png)) as normalized:
        assert normalized.format == "PNG"
        assert normalized.mode == "RGB"
        assert normalized.info == {}


def test_uses_exif_transposed_dimensions_in_ocr_result() -> None:
    source = Image.new("RGB", (2, 3), "white")
    exif = source.getexif()
    exif[274] = 6
    payload = io.BytesIO()
    source.save(payload, "JPEG", exif=exif)
    engine = RecordingEngine()

    result = OcrService(engine=engine).extract(payload.getvalue(), "image/jpeg")

    assert (result.width, result.height) == (3, 2)
    assert engine.normalized_png is not None
    with Image.open(io.BytesIO(engine.normalized_png)) as normalized:
        assert normalized.size == (3, 2)


@pytest.mark.parametrize("text", ["", " \n\t "])
def test_rejects_blank_ocr_output(text: str) -> None:
    service = OcrService(engine=RecordingEngine(text))
    with pytest.raises(NoTextDetectedError):
        service.extract(image_bytes(), "image/png")


def test_rejects_ocr_output_over_the_text_limit() -> None:
    service = OcrService(engine=RecordingEngine("four"), policy=ImagePolicy(max_text_chars=3))
    with pytest.raises(OcrError, match="text exceeds"):
        service.extract(image_bytes(), "image/png")


def test_tesseract_uses_shell_free_stdin_stdout_invocation() -> None:
    captured: dict[str, object] = {}

    def runner(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[bytes]:
        captured["command"] = command
        captured.update(kwargs)
        return subprocess.CompletedProcess(command, 0, stdout=b"detected text\n", stderr=b"")

    engine = TesseractOcrEngine(
        executable="safe-tesseract", languages="eng+hin", runner=runner
    )
    assert engine.extract_text(b"normalized-png", timeout_seconds=9) == "detected text\n"
    assert captured["command"] == [
        "safe-tesseract",
        "stdin",
        "stdout",
        "-l",
        "eng+hin",
        "--psm",
        "6",
    ]
    assert captured["input"] == b"normalized-png"
    assert captured["timeout"] == 9
    assert captured["shell"] is False
    assert captured["stdout"] is subprocess.PIPE
    assert captured["stderr"] is subprocess.PIPE
    assert captured["check"] is False


def test_tesseract_maps_missing_executable_to_unavailable() -> None:
    def runner(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[bytes]:
        raise FileNotFoundError(command[0])
    with pytest.raises(OcrUnavailableError):
        TesseractOcrEngine(runner=runner).extract_text(b"png", timeout_seconds=1)


def test_tesseract_maps_timeout_to_domain_error() -> None:
    def runner(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[bytes]:
        raise subprocess.TimeoutExpired(command, 1)
    with pytest.raises(OcrTimeoutError):
        TesseractOcrEngine(runner=runner).extract_text(b"png", timeout_seconds=1)


def test_tesseract_maps_nonzero_exit_to_unavailable() -> None:
    def runner(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[bytes]:
        return subprocess.CompletedProcess(command, 1, stdout=b"", stderr=b"missing language")
    with pytest.raises(OcrUnavailableError) as error:
        TesseractOcrEngine(runner=runner).extract_text(b"png", timeout_seconds=1)
    assert str(error.value) == "Tesseract failed"
    assert "missing language" not in str(error.value)
