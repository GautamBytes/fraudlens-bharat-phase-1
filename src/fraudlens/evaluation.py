"""Reproducible, leakage-safe Phase 2 classifier evaluation."""

import argparse
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Any, Dict, Iterable, List, Mapping, Sequence, Tuple

import numpy as np
from sklearn.calibration import CalibratedClassifierCV
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, confusion_matrix, precision_recall_fscore_support

from fraudlens.config import DATASET_PATH
from fraudlens.data_contract import PHASE2_TARGET_PER_LABEL, TRAINED_LABELS
from fraudlens.model_training import _fit_deterministic_vectorizer, _select_threshold, load_dataset
from fraudlens.preprocessing import CATEGORY_MARKERS, STRONG_CATEGORY_MARKERS, _contains_keyword, prepare_model_text


CLASSIFIER_NAMES = ("calibrated_tfidf", "marker_tfidf", "raw_tfidf", "rule_only")
SPLITS = ("train", "validation", "test")
_FLOAT_DIGITS = 8


@dataclass(frozen=True)
class EvaluationBundle:
    """Immutable evaluation document plus deterministic on-disk evidence."""

    document: Mapping[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        """Return a detached, JSON-compatible copy of the immutable document."""
        return json.loads(json.dumps(_thaw(self.document), sort_keys=True))


def evaluate_all(dataset_path: Path, output_dir: Path) -> EvaluationBundle:
    """Evaluate four fixed baselines without fitting or selecting on the test split."""
    dataset_path = Path(dataset_path)
    output_dir = Path(output_dir)
    frame = load_dataset(dataset_path)
    split_frames = {name: frame.loc[frame["split"] == name].copy() for name in SPLITS}
    for name, split in split_frames.items():
        if split.empty:
            raise ValueError("Phase 2 dataset has no {} rows".format(name))

    labels = sorted(split_frames["train"]["label"].unique().tolist())
    _ensure_split_labels(split_frames, labels)
    label_ids = {label: index for index, label in enumerate(labels)}
    y_by_split = {
        name: np.asarray([label_ids[label] for label in split["label"].tolist()], dtype=int)
        for name, split in split_frames.items()
    }
    documents: Dict[str, Any] = {}
    documents["rule_only"] = _evaluate_rule(split_frames, y_by_split, labels)
    documents["raw_tfidf"] = _evaluate_tfidf(
        split_frames, y_by_split, labels, text_column="model_text", calibrated=False
    )
    documents["marker_tfidf"] = _evaluate_tfidf(
        split_frames, y_by_split, labels, text_column="marker_text", calibrated=False
    )
    documents["calibrated_tfidf"] = _evaluate_tfidf(
        split_frames, y_by_split, labels, text_column="model_text", calibrated=True
    )

    present_labels = sorted(frame["label"].unique().tolist())
    target_met = all(
        int((frame["label"] == label).sum()) >= PHASE2_TARGET_PER_LABEL
        for label in TRAINED_LABELS
    )
    document = {
        "schema_version": 1,
        "dataset": {
            "sha256": _sha256(dataset_path),
            "rows": int(len(frame)),
            "split_rows": {name: int(len(split_frames[name])) for name in SPLITS},
            "present_labels": present_labels,
            "missing_labels": sorted(TRAINED_LABELS - set(present_labels)),
            "phase2_target_per_label": PHASE2_TARGET_PER_LABEL,
            "phase2_target_met": target_met,
            "limitation": (
                "Synthetic bootstrap only: legitimate is absent and no supported label "
                "has {} rows.".format(PHASE2_TARGET_PER_LABEL)
            ),
        },
        "protocol": {
            "train": "fit vectorizers, models, and calibration only",
            "validation": "select abstention threshold only",
            "test": "single untouched frozen evaluation",
            "random_seed": 42,
            "marker_tfidf": "ablation only; not selected for runtime use",
            "latency": "Wall-clock timing is omitted so evidence bytes remain reproducible.",
        },
        "classifiers": {name: documents[name] for name in CLASSIFIER_NAMES},
    }
    bundle = EvaluationBundle(document=_freeze(document))
    _write_outputs(bundle, output_dir)
    return bundle


def _evaluate_tfidf(
    split_frames: Mapping[str, Any],
    y_by_split: Mapping[str, np.ndarray],
    labels: Sequence[str],
    text_column: str,
    calibrated: bool,
) -> Dict[str, Any]:
    train_text = _texts(split_frames["train"], text_column)
    vectorizer, train_features = _fit_deterministic_vectorizer(train_text)
    features = {
        "validation": vectorizer.transform(_texts(split_frames["validation"], text_column)),
        "test": vectorizer.transform(_texts(split_frames["test"], text_column)),
    }
    base = LogisticRegression(max_iter=1000, class_weight="balanced", random_state=42)
    if calibrated:
        classifier = CalibratedClassifierCV(estimator=base, method="sigmoid", cv=3)
    else:
        classifier = base
    classifier.fit(train_features, y_by_split["train"])
    validation_probabilities = classifier.predict_proba(features["validation"])
    threshold = _select_threshold(y_by_split["validation"], validation_probabilities)
    test_probabilities = classifier.predict_proba(features["test"])
    name = "calibrated_tfidf" if calibrated else (
        "marker_tfidf" if text_column == "marker_text" else "raw_tfidf"
    )
    return {
        "kind": "tfidf_logistic_regression",
        "selection_status": "selected" if name == "calibrated_tfidf" else (
            "ablation_not_selected" if name == "marker_tfidf" else "baseline_not_selected"
        ),
        "text_representation": (
            "raw_normalized_text" if text_column == "model_text" else "raw_normalized_text_plus_markers"
        ),
        "calibration": "sigmoid_cv_3_train_only" if calibrated else "none",
        "fit_split": "train",
        "split_rows": _split_rows(split_frames),
        "threshold": threshold,
        "threshold_selected_on": "validation",
        "validation": _metrics(
            "validation", y_by_split["validation"], validation_probabilities, threshold, labels
        ),
        "test": _metrics("test", y_by_split["test"], test_probabilities, threshold, labels),
    }


def _evaluate_rule(
    split_frames: Mapping[str, Any],
    y_by_split: Mapping[str, np.ndarray],
    labels: Sequence[str],
) -> Dict[str, Any]:
    validation_probabilities, validation_evidence = _rule_probabilities(
        _texts(split_frames["validation"], "model_text"), labels
    )
    threshold = _select_threshold(y_by_split["validation"], validation_probabilities)
    test_probabilities, test_evidence = _rule_probabilities(
        _texts(split_frames["test"], "model_text"), labels
    )
    return {
        "kind": "transparent_keyword_rule",
        "selection_status": "baseline_not_selected",
        "text_representation": "raw_normalized_text",
        "calibration": "none",
        "fit_split": "none; deterministic rules",
        "split_rows": _split_rows(split_frames),
        "threshold": threshold,
        "threshold_selected_on": "validation",
        "validation": _metrics(
            "validation", y_by_split["validation"], validation_probabilities, threshold,
            labels, validation_evidence,
        ),
        "test": _metrics("test", y_by_split["test"], test_probabilities, threshold, labels, test_evidence),
    }


def _rule_probabilities(texts: Sequence[str], labels: Sequence[str]) -> Tuple[np.ndarray, np.ndarray]:
    probabilities = np.zeros((len(texts), len(labels)), dtype=float)
    evidence = np.zeros(len(texts), dtype=bool)
    for row, text in enumerate(texts):
        scores = []
        for label in labels:
            marker_hits = sum(_contains_keyword(text, marker) for marker in CATEGORY_MARKERS.get(label, ()))
            strong_hits = sum(_contains_keyword(text, marker) for marker in STRONG_CATEGORY_MARKERS.get(label, ()))
            scores.append(float(marker_hits + 3 * strong_hits))
        strongest = max(scores)
        if strongest <= 0:
            probabilities[row, :] = 1.0 / len(labels)
            continue
        evidence[row] = True
        winning = [index for index, score in enumerate(scores) if score == strongest]
        probabilities[row, winning] = 1.0 / len(winning)
    return probabilities, evidence


def _metrics(
    split: str,
    y_true: np.ndarray,
    probabilities: np.ndarray,
    threshold: float,
    labels: Sequence[str],
    evidence: np.ndarray = None,
) -> Dict[str, Any]:
    predicted = probabilities.argmax(axis=1)
    confidence = probabilities.max(axis=1)
    accepted = confidence >= threshold
    if evidence is not None:
        accepted = np.logical_and(accepted, evidence)
    precision, recall, f1, support = precision_recall_fscore_support(
        y_true, predicted, labels=list(range(len(labels))), zero_division=0
    )
    per_class = {
        label: {
            "precision": _number(precision[index]),
            "recall": _number(recall[index]),
            "f1": _number(f1[index]),
            "support": int(support[index]),
        }
        for index, label in enumerate(labels)
    }
    coverage = _number(accepted.mean())
    accepted_accuracy = (
        _number(accuracy_score(y_true[accepted], predicted[accepted])) if accepted.any() else None
    )
    return {
        "split": split,
        "rows": int(len(y_true)),
        "accuracy": _number(accuracy_score(y_true, predicted)),
        "macro_precision": _number(float(np.mean(precision))),
        "macro_recall": _number(float(np.mean(recall))),
        "macro_f1": _number(float(np.mean(f1))),
        "per_class": per_class,
        "confusion_matrix_labels": list(labels),
        "confusion_matrix": confusion_matrix(y_true, predicted, labels=list(range(len(labels)))).tolist(),
        "expected_calibration_error": _expected_calibration_error(y_true, predicted, confidence),
        "coverage": coverage,
        "abstention_rate": _number(1.0 - coverage),
        "accepted_accuracy": accepted_accuracy,
        "latency": {
            "method": "not measured; wall-clock excluded from deterministic evidence",
            "unit": "milliseconds_per_row",
            "value": None,
        },
    }


def _expected_calibration_error(
    y_true: np.ndarray, predicted: np.ndarray, confidence: np.ndarray, bins: int = 10
) -> float:
    total = len(y_true)
    error = 0.0
    for bin_number in range(bins):
        lower = bin_number / bins
        upper = (bin_number + 1) / bins
        in_bin = (confidence >= lower) & (confidence <= upper if bin_number == bins - 1 else confidence < upper)
        if not in_bin.any():
            continue
        accuracy = (predicted[in_bin] == y_true[in_bin]).mean()
        error += abs(float(accuracy) - float(confidence[in_bin].mean())) * (in_bin.sum() / total)
    return _number(error)


def _ensure_split_labels(split_frames: Mapping[str, Any], labels: Sequence[str]) -> None:
    expected = set(labels)
    for name, split in split_frames.items():
        unseen = sorted(set(split["label"].tolist()) - expected)
        if unseen:
            raise ValueError("{} split has labels absent from train: {}".format(name, ", ".join(unseen)))


def _split_rows(split_frames: Mapping[str, Any]) -> Dict[str, int]:
    return {name: int(len(split_frames[name])) for name in SPLITS}


def _texts(frame: Any, column: str) -> Any:
    if column == "marker_text":
        return frame["model_text"].map(prepare_model_text)
    return frame[column]


def _number(value: Any) -> float:
    return round(float(value), _FLOAT_DIGITS)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _freeze(value: Any) -> Any:
    if isinstance(value, dict):
        return MappingProxyType({key: _freeze(item) for key, item in value.items()})
    if isinstance(value, list):
        return tuple(_freeze(item) for item in value)
    return value


def _thaw(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {key: _thaw(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_thaw(item) for item in value]
    return value


def _write_outputs(bundle: EvaluationBundle, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    document = bundle.to_dict()
    (output_dir / "evaluation.json").write_text(
        json.dumps(document, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8"
    )
    (output_dir / "summary.txt").write_text(_summary(document), encoding="utf-8")


def _summary(document: Mapping[str, Any]) -> str:
    dataset = document["dataset"]
    lines = [
        "FraudLens Phase 2 reproducible evaluation",
        "dataset_sha256: {}".format(dataset["sha256"]),
        "rows: {} (train={train}, validation={validation}, test={test})".format(
            dataset["rows"], **dataset["split_rows"]
        ),
        "present_labels: {}".format(", ".join(dataset["present_labels"])),
        "missing_labels: {}".format(", ".join(dataset["missing_labels"]) or "none"),
        "phase2_target_met: {}".format(str(dataset["phase2_target_met"]).lower()),
        "",
        "Test split results (raw predicted-label metrics; abstentions reported separately):",
    ]
    for name in CLASSIFIER_NAMES:
        metrics = document["classifiers"][name]["test"]
        lines.append(
            "{name}: accuracy={accuracy:.4f} macro_f1={macro_f1:.4f} coverage={coverage:.4f} "
            "abstention={abstention_rate:.4f} accepted_accuracy={accepted}".format(
                name=name,
                accepted=("n/a" if metrics["accepted_accuracy"] is None else "{:.4f}".format(metrics["accepted_accuracy"])),
                **metrics
            )
        )
    lines.extend(["", "Limitation: {}".format(dataset["limitation"]), ""])
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, default=DATASET_PATH)
    parser.add_argument("--output", type=Path, default=Path("outputs/phase2"))
    args = parser.parse_args()
    bundle = evaluate_all(args.dataset, args.output)
    print(_summary(bundle.to_dict()), end="")


if __name__ == "__main__":
    main()
