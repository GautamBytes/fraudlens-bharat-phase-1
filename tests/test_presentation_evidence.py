import importlib
import importlib.util
import json
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
EXPECTED_IMAGES = {
    "final_system_architecture.png",
    "model_comparison.png",
    "robustness_ablation.png",
    "runtime_confusion_matrix.png",
}


def _module():
    spec = importlib.util.find_spec("fraudlens.presentation_evidence")
    assert spec is not None
    return importlib.import_module("fraudlens.presentation_evidence")


def test_presentation_evidence_uses_current_runtime_and_research_metrics(tmp_path):
    module = _module()

    written = module.generate_presentation_evidence(ROOT, tmp_path)
    payload = json.loads((tmp_path / "final_evidence.json").read_text(encoding="utf-8"))

    assert {path.name for path in written} == {"final_evidence.json", *EXPECTED_IMAGES}
    assert payload["dataset"] == {
        "rows": 64,
        "train_rows": 48,
        "validation_rows": 8,
        "test_rows": 8,
        "synthetic_only": True,
        "legitimate_label_present": False,
        "phase2_target_met": False,
    }
    assert payload["deployed_runtime"] == {
        "name": "calibrated_tfidf",
        "accuracy": 0.5,
        "macro_f1": 0.5,
        "coverage": 0.875,
        "abstention_rate": 0.125,
        "accepted_accuracy": 0.57142857,
    }
    character = next(
        row
        for row in payload["research_candidates"]
        if row["model"] == "character_tfidf_logistic_regression"
    )
    assert character["accuracy"] == 0.75
    assert character["macro_f1"] == 0.66666667
    assert payload["runtime_labels"][-1] == "unknown"
    assert len(payload["runtime_confusion_matrix"]) == 9
    assert all(len(row) == 9 for row in payload["runtime_confusion_matrix"])
    assert payload["claim_boundary"] == (
        "Internal synthetic evidence only; the research candidate is not the deployed model "
        "and no production-accuracy claim is made."
    )
    for image_name in EXPECTED_IMAGES:
        with Image.open(tmp_path / image_name) as image:
            assert image.format == "PNG"
            assert image.width >= 1600
            assert image.height >= 1000


def test_committed_presentation_manifest_matches_fresh_generation(tmp_path):
    module = _module()
    module.generate_presentation_evidence(ROOT, tmp_path)

    assert (tmp_path / "final_evidence.json").read_bytes() == (
        ROOT / "outputs" / "presentation" / "final_evidence.json"
    ).read_bytes()


def test_ci_regenerates_presentation_evidence_manifest():
    workflow = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")

    assert "Verify current presentation evidence" in workflow
    assert "fraudlens.presentation_evidence" in workflow
    assert 'cmp "$presentation_tmp/final_evidence.json"' in workflow
    assert '"outputs/presentation/final_evidence.json"' in workflow
