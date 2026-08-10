"""Generate current, source-traceable presentation evidence for the final capstone."""

import argparse
import csv
import hashlib
import json
from pathlib import Path
from typing import Optional, Sequence

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from matplotlib.patches import FancyBboxPatch


_NAVY = "#102A43"
_TEAL = "#0F8B8D"
_ORANGE = "#F29E4C"
_RED = "#C44536"
_BLUE = "#2F6BFF"
_CREAM = "#F7F9FC"
_CLAIM_BOUNDARY = (
    "Internal synthetic evidence only; the research candidate is not the deployed model "
    "and no production-accuracy claim is made."
)


def _read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _read_csv(path: Path):
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def _number(value: str):
    if value == "":
        return None
    return round(float(value), 8)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _build_payload(repo_root: Path):
    metrics_path = repo_root / "models" / "metrics.json"
    evaluation_path = repo_root / "outputs" / "phase2" / "evaluation.json"
    comparison_path = repo_root / "outputs" / "research" / "classification_summary.csv"
    robustness_path = repo_root / "outputs" / "research" / "ablation_summary.csv"
    metrics = _read_json(metrics_path)
    evaluation = _read_json(evaluation_path)
    comparison_rows = _read_csv(comparison_path)
    robustness_rows = _read_csv(robustness_path)
    dataset = evaluation["dataset"]
    test_metrics = metrics["test"]
    final_runtime_evaluation = evaluation["classifiers"]["calibrated_tfidf"]["test"]
    research_candidates = []
    for row in comparison_rows:
        research_candidates.append(
            {
                "model": row["model"],
                "accuracy": _number(row["accuracy"]),
                "balanced_accuracy": _number(row["balanced_accuracy"]),
                "macro_f1": _number(row["macro_f1"]),
                "mcc": _number(row["mcc"]),
                "coverage": _number(row["coverage"]),
                "accepted_accuracy": _number(row["accepted_accuracy"]),
                "estimated_model_bytes": int(row["estimated_model_bytes"]),
            }
        )
    robustness = [
        {
            "model": row["model"],
            "condition": row["condition"],
            "accuracy": _number(row["accuracy"]),
            "macro_f1": _number(row["macro_f1"]),
            "coverage": _number(row["coverage"]),
            "macro_f1_drop_from_clean": _number(row["macro_f1_drop_from_clean"]),
        }
        for row in robustness_rows
    ]
    return {
        "schema_version": 1,
        "dataset": {
            "rows": dataset["rows"],
            "train_rows": dataset["split_rows"]["train"],
            "validation_rows": dataset["split_rows"]["validation"],
            "test_rows": dataset["split_rows"]["test"],
            "synthetic_only": True,
            "legitimate_label_present": "legitimate" not in dataset["missing_labels"],
            "phase2_target_met": dataset["phase2_target_met"],
        },
        "deployed_runtime": {
            "name": "calibrated_tfidf",
            "accuracy": round(test_metrics["overall_accuracy_with_abstentions"], 8),
            "macro_f1": round(test_metrics["macro_f1_all_predictions"], 8),
            "coverage": round(test_metrics["coverage"], 8),
            "abstention_rate": round(test_metrics["abstention_rate"], 8),
            "accepted_accuracy": round(test_metrics["accepted_accuracy"], 8),
        },
        "runtime_confusion_matrix": final_runtime_evaluation["confusion_matrix"],
        "runtime_labels": final_runtime_evaluation["confusion_matrix_labels"],
        "research_candidates": research_candidates,
        "robustness": robustness,
        "claim_boundary": _CLAIM_BOUNDARY,
        "sources": {
            str(path.relative_to(repo_root)): _sha256(path)
            for path in (metrics_path, evaluation_path, comparison_path, robustness_path)
        },
    }


def _save_figure(fig, output_path: Path) -> Path:
    fig.savefig(
        output_path,
        dpi=160,
        facecolor="white",
        bbox_inches=None,
        metadata={"Software": "FraudLens Bharat deterministic evidence generator"},
    )
    plt.close(fig)
    return output_path


def _architecture_figure(output_path: Path) -> Path:
    fig, axis = plt.subplots(figsize=(12, 9))
    axis.set_xlim(0, 12)
    axis.set_ylim(0, 9)
    axis.axis("off")
    fig.patch.set_facecolor(_CREAM)

    def box(x, y, width, height, title, detail, color):
        patch = FancyBboxPatch(
            (x, y), width, height,
            boxstyle="round,pad=0.03,rounding_size=0.12",
            linewidth=2, edgecolor=color, facecolor="white",
        )
        axis.add_patch(patch)
        axis.text(x + 0.18, y + height - 0.32, title, fontsize=12, fontweight="bold", color=_NAVY)
        axis.text(x + 0.18, y + 0.25, detail, fontsize=9.5, color="#334E68", va="bottom")

    def arrow(x1, y1, x2, y2):
        axis.annotate("", xy=(x2, y2), xytext=(x1, y1), arrowprops={"arrowstyle": "->", "lw": 2, "color": "#627D98"})

    axis.text(0.6, 8.5, "FraudLens Bharat - Final Phase 1 + Phase 2 Architecture", fontsize=21, fontweight="bold", color=_NAVY)
    axis.text(0.6, 8.12, "One shared analysis path; storage is optional and privacy-bounded", fontsize=11, color="#486581")
    box(0.7, 6.6, 2.0, 1.0, "Text input", "FastAPI / Streamlit", _BLUE)
    box(0.7, 4.9, 2.0, 1.0, "Screenshot", "PNG/JPEG, bounded", _TEAL)
    box(3.35, 4.9, 2.15, 1.0, "Local OCR", "Tesseract eng+hin", _TEAL)
    box(3.35, 6.6, 2.15, 1.0, "Preprocess", "Normalize text", _BLUE)
    box(6.1, 6.8, 2.25, 1.0, "Classifier", "Calibrated TF-IDF", _ORANGE)
    box(6.1, 5.35, 2.25, 1.0, "Evidence", "Entities + URL checks", _ORANGE)
    box(6.1, 3.9, 2.25, 1.0, "Risk & draft", "Reasons + complaint", _ORANGE)
    box(9.0, 6.0, 2.25, 1.15, "API + dashboard", "Result + provenance", _BLUE)
    box(9.0, 4.1, 2.25, 1.15, "Consent storage", "SQLite + retention", _RED)
    box(9.0, 2.2, 2.25, 1.15, "Entity graph", "HMAC IDs + masks", _TEAL)
    box(3.35, 2.2, 4.95, 1.0, "Release boundary", "Readiness, safe logs, non-root read-only containers", _NAVY)
    arrow(2.7, 7.1, 3.35, 7.1)
    arrow(2.7, 5.4, 3.35, 5.4)
    arrow(4.45, 5.9, 4.45, 6.6)
    arrow(5.5, 7.1, 6.1, 7.3)
    arrow(5.5, 7.0, 6.1, 5.85)
    arrow(8.35, 7.3, 9.0, 6.65)
    arrow(8.35, 5.85, 9.0, 6.4)
    arrow(8.35, 4.4, 9.0, 6.2)
    arrow(10.1, 6.0, 10.1, 5.25)
    arrow(10.1, 4.1, 10.1, 3.35)
    arrow(8.3, 2.7, 9.0, 2.7)
    axis.text(
        0.7, 0.7,
        "Blue: Phase 1 foundation     Teal/red: Phase 2 OCR, graph, calibrated evaluation, privacy and release hardening",
        fontsize=10.5, fontweight="bold", color=_NAVY,
    )
    axis.text(0.7, 0.28, "Assistive local prototype - no automatic filing, GNN or production-accuracy claim", fontsize=10, color=_RED)
    return _save_figure(fig, output_path)


def _comparison_figure(payload, output_path: Path) -> Path:
    rows = payload["research_candidates"]
    labels = ["Rules", "Word", "Character", "Word + char", "Calibrated hybrid"]
    x = np.arange(len(rows))
    width = 0.25
    fig, axis = plt.subplots(figsize=(12, 9))
    axis.bar(x - width, [row["accuracy"] for row in rows], width, label="Accuracy", color=_BLUE)
    axis.bar(x, [row["macro_f1"] for row in rows], width, label="Macro-F1", color=_TEAL)
    axis.bar(x + width, [row["coverage"] for row in rows], width, label="Coverage", color=_ORANGE)
    axis.set_xticks(x, labels, rotation=12, ha="right")
    axis.set_ylim(0, 1.08)
    axis.set_ylabel("Score")
    axis.set_title("Same-split lightweight research comparison", loc="left", fontsize=20, fontweight="bold", color=_NAVY)
    axis.grid(axis="y", alpha=0.2)
    axis.legend(loc="upper left", ncols=3)
    deployed = payload["deployed_runtime"]
    axis.text(
        0.01, -0.22,
        "Deployed calibrated runtime (separate): accuracy {:.2f}, Macro-F1 {:.2f}, coverage {:.1%}.\n{}".format(
            deployed["accuracy"], deployed["macro_f1"], deployed["coverage"], payload["claim_boundary"]
        ),
        transform=axis.transAxes, fontsize=10, color="#334E68", va="top",
    )
    fig.subplots_adjust(left=0.10, right=0.97, top=0.90, bottom=0.25)
    return _save_figure(fig, output_path)


def _robustness_figure(payload, output_path: Path) -> Path:
    models = []
    conditions = []
    for row in payload["robustness"]:
        if row["model"] not in models:
            models.append(row["model"])
        if row["condition"] not in conditions:
            conditions.append(row["condition"])
    matrix = np.array([
        [
            next(row["macro_f1"] for row in payload["robustness"] if row["model"] == model and row["condition"] == condition)
            for condition in conditions
        ]
        for model in models
    ])
    model_labels = ["Rules", "Word", "Character", "Word + char", "Calibrated hybrid"]
    condition_labels = [condition.replace("_", " ") for condition in conditions]
    fig, axis = plt.subplots(figsize=(12, 9))
    sns.heatmap(
        matrix, annot=True, fmt=".3f", cmap="YlGnBu", vmin=0, vmax=0.75,
        xticklabels=condition_labels, yticklabels=model_labels, cbar_kws={"label": "Macro-F1"}, ax=axis,
    )
    axis.set_title("Robustness under deterministic language and OCR noise", loc="left", fontsize=20, fontweight="bold", color=_NAVY, pad=18)
    axis.set_xlabel("Condition")
    axis.set_ylabel("Research candidate")
    axis.tick_params(axis="x", rotation=28)
    fig.text(0.08, 0.03, "Eight-row synthetic frozen test; perturbations are simulations, not a labelled OCR benchmark.", fontsize=10, color="#486581")
    fig.subplots_adjust(left=0.20, right=0.94, top=0.88, bottom=0.20)
    return _save_figure(fig, output_path)


def _confusion_figure(payload, output_path: Path) -> Path:
    labels = [label.replace("_", " ") for label in payload["runtime_labels"]]
    matrix = np.array(payload["runtime_confusion_matrix"])
    fig, axis = plt.subplots(figsize=(12, 9))
    sns.heatmap(matrix, annot=True, fmt="d", cmap="Blues", cbar=False, xticklabels=labels, yticklabels=labels, ax=axis, linewidths=0.5)
    axis.set_title("Deployed calibrated runtime - frozen test confusion matrix", loc="left", fontsize=19, fontweight="bold", color=_NAVY, pad=18)
    axis.set_xlabel("Final prediction (abstentions are unknown overall errors)")
    axis.set_ylabel("True label")
    axis.tick_params(axis="x", rotation=34)
    axis.tick_params(axis="y", rotation=0)
    fig.text(0.10, 0.03, "8 synthetic rows, one per fraud class | Accuracy 0.500 | Macro-F1 0.500 | Coverage 0.875", fontsize=10, color="#486581")
    fig.subplots_adjust(left=0.22, right=0.96, top=0.87, bottom=0.25)
    return _save_figure(fig, output_path)


def generate_presentation_evidence(repo_root: Path, output_dir: Path):
    repo_root = Path(repo_root)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    payload = _build_payload(repo_root)
    manifest_path = output_dir / "final_evidence.json"
    manifest_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    written = [manifest_path]
    written.append(_architecture_figure(output_dir / "final_system_architecture.png"))
    written.append(_comparison_figure(payload, output_dir / "model_comparison.png"))
    written.append(_robustness_figure(payload, output_dir / "robustness_ablation.png"))
    written.append(_confusion_figure(payload, output_dir / "runtime_confusion_matrix.png"))
    return tuple(written)


def main(argv: Optional[Sequence[str]] = None) -> None:
    parser = argparse.ArgumentParser(description="Generate current final-presentation evidence")
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    for path in generate_presentation_evidence(args.repo_root, args.output):
        print("wrote {}".format(path))


if __name__ == "__main__":
    main()
