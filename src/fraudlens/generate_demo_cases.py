import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Sequence

from PIL import Image, ImageDraw, ImageFont

from fraudlens.analysis_service import (
    AnalysisInput,
    DatabaseCaseStore,
    create_analysis_service,
    resolve_predictor,
)
from fraudlens.config import DEMO_CASES_DIR
from fraudlens.demo_cases import DEMO_CASES as DEMO_CASE_CATALOG
from fraudlens.settings import Settings


DEMO_CASES = {case.slug: case.text for case in DEMO_CASE_CATALOG}
_DEMO_TIMESTAMP = datetime(2026, 8, 10, 12, 0, 0)
_GRAPH_DEMO_MESSAGES = (
    (
        "graph-demo-1",
        "Urgent KYC verification required at https://fraud-demo.example/claim today.",
    ),
    (
        "graph-demo-2",
        "Your courier package is detained. Pay customs delivery fee at "
        "https://fraud-demo.example/claim to release parcel.",
    ),
)


def _dump(result):
    if hasattr(result, "model_dump"):
        return result.model_dump(mode="json")
    return json.loads(result.json())


def generate_demo_cases(output_dir: Path):
    output_dir.mkdir(parents=True, exist_ok=True)
    settings = Settings.from_env()
    predictor = resolve_predictor(settings)
    written = []
    for name, text in DEMO_CASES.items():
        service = create_analysis_service(
            settings=settings,
            predictor=predictor,
            clock=lambda: _DEMO_TIMESTAMP,
            id_generator=lambda name=name: "demo-{}".format(name),
        )
        result = service.analyze(AnalysisInput(text=text, store_case=False))
        output_path = output_dir / f"{name}.json"
        output_path.write_text(json.dumps(_dump(result), indent=2), encoding="utf-8")
        written.append(output_path)
    return tuple(written)


def prepare_graph_demo_database(database_path: Path):
    """Store two synthetic cases sharing one safe example-domain URL."""

    settings = Settings.from_env()
    predictor = resolve_predictor(settings)
    store = DatabaseCaseStore(database_path)
    results = []
    for case_id, text in _GRAPH_DEMO_MESSAGES:
        service = create_analysis_service(
            settings=settings,
            predictor=predictor,
            store=store,
            id_generator=lambda case_id=case_id: case_id,
        )
        results.append(service.analyze(AnalysisInput(text=text, store_case=True)))
    return tuple(results)


def generate_ocr_demo_screenshot(output_path: Path) -> Path:
    """Create a metadata-free synthetic screenshot for the OCR demo."""

    image = Image.new("RGB", (1200, 500), "white")
    draw = ImageDraw.Draw(image)
    heading_font = ImageFont.load_default(size=46)
    body_font = ImageFont.load_default(size=42)
    draw.text((64, 54), "SYNTHETIC DEMO - NO REAL PII", fill="#8B1E1E", font=heading_font)
    lines = (
        "Security alert: email login blocked.",
        "Reply with OTP and password",
        "to prove ownership.",
    )
    for index, line in enumerate(lines):
        draw.text((64, 158 + (index * 76)), line, fill="#111827", font=body_font)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(output_path, format="PNG", optimize=False, compress_level=9)
    return output_path


def main(argv: Optional[Sequence[str]] = ()) -> None:
    parser = argparse.ArgumentParser(description="Generate deterministic synthetic demo evidence")
    parser.add_argument("--output", type=Path, default=DEMO_CASES_DIR)
    parser.add_argument("--screenshot-output", type=Path)
    parser.add_argument("--graph-database", type=Path)
    args = parser.parse_args(argv)
    for output_path in generate_demo_cases(args.output):
        print("wrote {}".format(output_path.name))
    if args.screenshot_output is not None:
        output_path = generate_ocr_demo_screenshot(args.screenshot_output)
        print("wrote {}".format(output_path))
    if args.graph_database is not None:
        prepare_graph_demo_database(args.graph_database)
        print("prepared {}".format(args.graph_database))


if __name__ == "__main__":
    main(None)
