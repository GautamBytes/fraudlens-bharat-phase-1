import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Sequence

from fraudlens.analysis_service import AnalysisInput, AnalysisService, resolve_predictor
from fraudlens.config import DEMO_CASES_DIR
from fraudlens.demo_cases import DEMO_CASES as DEMO_CASE_CATALOG
from fraudlens.settings import Settings


DEMO_CASES = {case.slug: case.text for case in DEMO_CASE_CATALOG}
_DEMO_TIMESTAMP = datetime(2026, 8, 10, 12, 0, 0)


def _dump(result):
    if hasattr(result, "model_dump"):
        return result.model_dump(mode="json")
    return json.loads(result.json())


def generate_demo_cases(output_dir: Path):
    output_dir.mkdir(parents=True, exist_ok=True)
    predictor = resolve_predictor(Settings.from_env())
    written = []
    for name, text in DEMO_CASES.items():
        service = AnalysisService(
            predictor=predictor,
            clock=lambda: _DEMO_TIMESTAMP,
            id_generator=lambda name=name: "demo-{}".format(name),
        )
        result = service.analyze(AnalysisInput(text=text, store_case=False))
        output_path = output_dir / f"{name}.json"
        output_path.write_text(json.dumps(_dump(result), indent=2), encoding="utf-8")
        written.append(output_path)
    return tuple(written)


def main(argv: Optional[Sequence[str]] = ()) -> None:
    parser = argparse.ArgumentParser(description="Generate deterministic synthetic demo evidence")
    parser.add_argument("--output", type=Path, default=DEMO_CASES_DIR)
    args = parser.parse_args(argv)
    for output_path in generate_demo_cases(args.output):
        print("wrote {}".format(output_path.name))


if __name__ == "__main__":
    main(None)
