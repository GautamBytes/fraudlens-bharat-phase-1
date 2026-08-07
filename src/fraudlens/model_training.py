"""Deterministic training for the calibrated Phase 2 TF-IDF predictor."""

import argparse
import hashlib
import json
import platform
from pathlib import Path
from typing import Dict, Iterable, Tuple

import joblib
import numpy as np
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score
from sklearn.preprocessing import LabelEncoder

from fraudlens.config import (
    ARTIFACT_FILENAMES,
    ARTIFACT_MANIFEST_VERSION,
    ArtifactPaths,
    DATASET_PATH,
    DEFAULT_ARTIFACTS,
    PIPELINE_CODE_SOURCES,
    TRAINING_CONFIGURATION,
    artifact_paths,
    pipeline_code_sha256,
    release_model_version,
    training_configuration_sha256,
)
from fraudlens.data_contract import PHASE2_TARGET_PER_LABEL, TRAINED_LABELS, load_phase2_dataset
from fraudlens.preprocessing import normalize_text


SUPPORTED_BACKENDS = frozenset({"tfidf"})
SPLITS = ("train", "validation", "test")


def load_dataset(path: Path = DATASET_PATH) -> pd.DataFrame:
    """Load the immutable Phase 2 contract and use raw normalized text only."""
    frame = load_phase2_dataset(Path(path), minimum_per_label=0).copy()
    frame["model_text"] = frame["text"].map(normalize_text)
    return frame


def _dataset_sha256(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _file_sha256(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _runtime_versions() -> Dict[str, str]:
    import sklearn

    return {
        "python": platform.python_version(),
        "sklearn": str(sklearn.__version__),
        "joblib": str(joblib.__version__),
    }


def _split_frame(frame: pd.DataFrame, split: str) -> pd.DataFrame:
    result = frame.loc[frame["split"] == split].copy()
    if result.empty:
        raise ValueError("Phase 2 dataset has no {} rows".format(split))
    return result


def _fit_deterministic_vectorizer(train_text: pd.Series) -> Tuple[TfidfVectorizer, object]:
    """Fix vocabulary insertion order so serialized artifacts are reproducible."""
    options = dict(TRAINING_CONFIGURATION["vectorizer"])
    options["ngram_range"] = tuple(options["ngram_range"])
    prototype = TfidfVectorizer(**options)
    analyzer = prototype.build_analyzer()
    vocabulary_terms = sorted(
        {token for text in train_text.tolist() for token in analyzer(text)}
    )
    vocabulary = {term: index for index, term in enumerate(vocabulary_terms)}
    vectorizer = TfidfVectorizer(**options, vocabulary=vocabulary)
    return vectorizer, vectorizer.fit_transform(train_text)


def _select_threshold(y_true: np.ndarray, probabilities: np.ndarray) -> float:
    """Select on validation only, rewarding correct coverage and penalising errors."""
    confidences = probabilities.max(axis=1)
    predictions = probabilities.argmax(axis=1)
    candidates = sorted({0.0, 1.0, *[float(value) for value in confidences]})
    best: Tuple[float, float, float] = (-float("inf"), -float("inf"), -float("inf"))
    selected = 1.0
    for threshold in candidates:
        accepted = confidences >= threshold
        correct = int(np.logical_and(accepted, predictions == y_true).sum())
        incorrect = int(np.logical_and(accepted, predictions != y_true).sum())
        coverage = float(accepted.mean())
        # A wrong alert is worse than a transparent abstention; ties favour coverage.
        score = float(correct - incorrect) / len(y_true)
        candidate = (score, coverage, -threshold)
        if candidate > best:
            best = candidate
            selected = float(threshold)
    return round(selected, 8)


def _evaluation(
    y_true: np.ndarray,
    probabilities: np.ndarray,
    threshold: float,
    labels: Iterable[int],
    label_names: Iterable[str],
) -> Dict[str, object]:
    predicted = probabilities.argmax(axis=1)
    confidence = probabilities.max(axis=1)
    accepted = confidence >= threshold
    covered_true = y_true[accepted]
    covered_predicted = predicted[accepted]
    coverage = float(accepted.mean())
    accepted_accuracy = (
        float(accuracy_score(covered_true, covered_predicted)) if accepted.any() else None
    )
    return {
        "rows": int(len(y_true)),
        "coverage": coverage,
        "abstention_rate": float(1.0 - coverage),
        "accepted_accuracy": accepted_accuracy,
        "overall_accuracy_with_abstentions": float(
            np.logical_and(accepted, predicted == y_true).mean()
        ),
        "macro_f1_all_predictions": float(
            f1_score(y_true, predicted, labels=list(labels), average="macro", zero_division=0)
        ),
        "classification_report": classification_report(
            y_true,
            predicted,
            labels=list(labels),
            target_names=list(label_names),
            output_dict=True,
            zero_division=0,
        ),
        "confusion_matrix": confusion_matrix(y_true, predicted, labels=list(labels)).tolist(),
    }


def train_baseline(
    dataset_path: Path = DATASET_PATH,
    artifact_dir: Path = None,
    backend: str = "tfidf",
) -> Dict[str, object]:
    """Train one calibrated classifier without crossing frozen Phase 2 splits."""
    if backend not in SUPPORTED_BACKENDS:
        raise ValueError("Unsupported backend: {}".format(backend))

    dataset_path = Path(dataset_path)
    artifacts: ArtifactPaths = artifact_paths(artifact_dir) if artifact_dir is not None else DEFAULT_ARTIFACTS
    artifacts.root.mkdir(parents=True, exist_ok=True)
    frame = load_dataset(dataset_path)
    splits = {name: _split_frame(frame, name) for name in SPLITS}

    train = splits["train"]
    validation = splits["validation"]
    test = splits["test"]
    train_labels = sorted(train["label"].unique())
    label_encoder = LabelEncoder().fit(train_labels)
    y_train = label_encoder.transform(train["label"])
    y_validation = label_encoder.transform(validation["label"])
    y_test = label_encoder.transform(test["label"])

    vectorizer, train_features = _fit_deterministic_vectorizer(train["model_text"])
    validation_features = vectorizer.transform(validation["model_text"])
    test_features = vectorizer.transform(test["model_text"])
    classifier = CalibratedClassifierCV(
        estimator=LogisticRegression(max_iter=1000, class_weight="balanced", random_state=42),
        method="sigmoid",
        cv=3,
    )
    classifier.fit(train_features, y_train)
    validation_probabilities = classifier.predict_proba(validation_features)
    threshold = _select_threshold(y_validation, validation_probabilities)
    test_probabilities = classifier.predict_proba(test_features)

    dataset_hash = _dataset_sha256(dataset_path)
    configuration_hash = training_configuration_sha256()
    pipeline_hash = pipeline_code_sha256()
    model_version = release_model_version(dataset_hash, configuration_hash, pipeline_hash)
    present_labels = sorted(frame["label"].unique())
    missing_labels = sorted(TRAINED_LABELS - set(present_labels))
    target_met = all(
        int((frame["label"] == label).sum()) >= PHASE2_TARGET_PER_LABEL
        for label in TRAINED_LABELS
    )
    label_ids = list(range(len(label_encoder.classes_)))
    validation_evaluation = _evaluation(
        y_validation, validation_probabilities, threshold, label_ids, label_encoder.classes_
    )
    test_evaluation = _evaluation(
        y_test, test_probabilities, threshold, label_ids, label_encoder.classes_
    )
    split_ids = {
        name: sorted(int(value) for value in split["id"].tolist()) for name, split in splits.items()
    }
    metadata: Dict[str, object] = {
        "backend": backend,
        "model_version": model_version,
        "dataset_sha256": dataset_hash,
        "dataset_filename": dataset_path.name,
        "dataset_rows": int(len(frame)),
        "split_rows": {name: int(len(split)) for name, split in splits.items()},
        "split_ids": split_ids,
        "present_labels": present_labels,
        "missing_labels": missing_labels,
        "phase2_target_per_label": PHASE2_TARGET_PER_LABEL,
        "phase2_target_met": target_met,
        "target_status": (
            "met" if target_met else
            "not_met; legitimate absent and bootstrap has fewer than 200 rows per label"
        ),
        "text_representation": "raw_normalized_text",
        "marker_enhancement_selected": False,
        "threshold": threshold,
        "training_configuration_sha256": configuration_hash,
        "pipeline_code_sha256": pipeline_hash,
        "pipeline_code_sources": list(PIPELINE_CODE_SOURCES),
        "runtime_versions": _runtime_versions(),
        "calibration": {
            "method": "sigmoid",
            "cv": 3,
            "training_only": True,
            "threshold_selected_on": "validation",
            "threshold_objective": "maximise correct-minus-incorrect coverage",
        },
        "evaluation": {
            "frozen_test_split": True,
            "validation": validation_evaluation,
            "test": test_evaluation,
        },
    }
    metrics: Dict[str, object] = {
        "dataset_rows": int(len(frame)),
        "split_rows": metadata["split_rows"],
        "model_version": model_version,
        "dataset_sha256": dataset_hash,
        "training_configuration_sha256": configuration_hash,
        "pipeline_code_sha256": pipeline_hash,
        "pipeline_code_sources": list(PIPELINE_CODE_SOURCES),
        "threshold": threshold,
        "test": test_evaluation,
    }
    joblib.dump(classifier, artifacts.model)
    # sklearn caches id(stop_words) for mutation detection; an address is not reproducible.
    vectorizer._stop_words_id = 0
    joblib.dump(vectorizer, artifacts.vectorizer)
    joblib.dump(label_encoder, artifacts.label_encoder)
    artifacts.metadata.write_text(json.dumps(metadata, indent=2, sort_keys=True), encoding="utf-8")
    artifacts.metrics.write_text(json.dumps(metrics, indent=2, sort_keys=True), encoding="utf-8")
    artifact_files = {
        artifacts.model.name: artifacts.model,
        artifacts.vectorizer.name: artifacts.vectorizer,
        artifacts.label_encoder.name: artifacts.label_encoder,
        artifacts.metadata.name: artifacts.metadata,
        artifacts.metrics.name: artifacts.metrics,
    }
    if tuple(artifact_files) != ARTIFACT_FILENAMES:
        raise ValueError("Artifact filenames do not match the trusted release layout")
    # The manifest is the tracked release trust anchor. It deliberately hashes
    # the five payload files but never itself, avoiding a circular hash.
    manifest = {
        "schema_version": ARTIFACT_MANIFEST_VERSION,
        "trust_anchor": "tracked-release-artifact-manifest",
        "artifacts": {
            name: {"sha256": _file_sha256(path)} for name, path in artifact_files.items()
        },
        "dataset": {
            "filename": dataset_path.name,
            "sha256": dataset_hash,
            "rows": int(len(frame)),
        },
        "model_version": model_version,
        "training_configuration_sha256": configuration_hash,
        "pipeline_code_sha256": pipeline_hash,
        "pipeline_code_sources": list(PIPELINE_CODE_SOURCES),
        "runtime_versions": _runtime_versions(),
    }
    artifacts.manifest.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    return metrics


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, default=DATASET_PATH)
    parser.add_argument("--backend", default="tfidf")
    args = parser.parse_args()
    metrics = train_baseline(dataset_path=args.dataset, backend=args.backend)
    print(json.dumps(metrics, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
