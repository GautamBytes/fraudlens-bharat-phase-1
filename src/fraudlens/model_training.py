import json
from pathlib import Path

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder

from fraudlens.config import (
    DATASET_PATH,
    LABEL_ENCODER_PATH,
    METRICS_DIR,
    METRICS_PATH,
    MODEL_PATH,
    MODELS_DIR,
    VECTORIZER_PATH,
)
from fraudlens.preprocessing import normalize_text, prepare_model_text


def load_dataset(path: Path = DATASET_PATH) -> pd.DataFrame:
    df = pd.read_csv(path)
    required = {"id", "text", "label", "source_type", "language_mix", "notes"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Dataset missing columns: {sorted(missing)}")
    df = df.dropna(subset=["text", "label"]).copy()
    df["cleaned_text"] = df["text"].map(normalize_text)
    df["model_text"] = df["text"].map(prepare_model_text)
    return df


def _can_stratify(labels: pd.Series, test_size: float) -> bool:
    counts = labels.value_counts()
    if counts.min() < 2:
        return False
    estimated_test_rows = int(round(len(labels) * test_size))
    return estimated_test_rows >= labels.nunique()


def train_baseline(dataset_path: Path = DATASET_PATH) -> dict:
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    METRICS_DIR.mkdir(parents=True, exist_ok=True)

    df = load_dataset(dataset_path)
    label_encoder = LabelEncoder()
    y = label_encoder.fit_transform(df["label"])

    stratify = y if _can_stratify(df["label"], 0.25) else None
    X_train, X_test, y_train, y_test = train_test_split(
        df["model_text"],
        y,
        test_size=0.25,
        random_state=42,
        stratify=stratify,
    )

    vectorizer = TfidfVectorizer(
        ngram_range=(1, 2),
        min_df=1,
        max_features=5000,
        sublinear_tf=True,
    )
    X_train_vec = vectorizer.fit_transform(X_train)
    X_test_vec = vectorizer.transform(X_test)

    classifier = LogisticRegression(max_iter=1000, class_weight="balanced", random_state=42)
    classifier.fit(X_train_vec, y_train)
    y_pred = classifier.predict(X_test_vec)

    labels = list(range(len(label_encoder.classes_)))
    target_names = list(label_encoder.classes_)
    report_dict = classification_report(
        y_test,
        y_pred,
        labels=labels,
        target_names=target_names,
        output_dict=True,
        zero_division=0,
    )
    report_text = classification_report(
        y_test,
        y_pred,
        labels=labels,
        target_names=target_names,
        zero_division=0,
    )
    matrix = confusion_matrix(y_test, y_pred, labels=labels)

    import joblib

    joblib.dump(classifier, MODEL_PATH)
    joblib.dump(vectorizer, VECTORIZER_PATH)
    joblib.dump(label_encoder, LABEL_ENCODER_PATH)

    metrics = {
        "dataset_rows": int(len(df)),
        "train_rows": int(len(X_train)),
        "test_rows": int(len(X_test)),
        "accuracy": float(report_dict["accuracy"]),
        "macro_f1": float(report_dict["macro avg"]["f1-score"]),
        "macro_precision": float(report_dict["macro avg"]["precision"]),
        "macro_recall": float(report_dict["macro avg"]["recall"]),
        "per_class": report_dict,
        "labels": target_names,
        "confusion_matrix": matrix.tolist(),
    }

    METRICS_PATH.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    (METRICS_DIR / "classification_report.txt").write_text(report_text, encoding="utf-8")
    _write_confusion_matrix_png(matrix, target_names)
    return metrics


def _write_confusion_matrix_png(matrix, target_names: list[str]) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(11, 8))
    image = ax.imshow(matrix, interpolation="nearest", cmap="Blues")
    fig.colorbar(image, ax=ax)
    ax.set(
        xticks=range(len(target_names)),
        yticks=range(len(target_names)),
        xticklabels=target_names,
        yticklabels=target_names,
        title="FraudLens Bharat Phase 1 Confusion Matrix",
        ylabel="Actual",
        xlabel="Predicted",
    )
    plt.setp(ax.get_xticklabels(), rotation=35, ha="right", rotation_mode="anchor")
    threshold = matrix.max() / 2 if matrix.size else 0
    for row_index in range(matrix.shape[0]):
        for col_index in range(matrix.shape[1]):
            color = "white" if matrix[row_index, col_index] > threshold else "black"
            ax.text(col_index, row_index, int(matrix[row_index, col_index]), ha="center", va="center", color=color)
    plt.tight_layout()
    plt.savefig(METRICS_DIR / "confusion_matrix.png", dpi=180)
    plt.close()


def main() -> None:
    metrics = train_baseline()
    print(json.dumps({k: metrics[k] for k in ["dataset_rows", "accuracy", "macro_f1", "macro_precision", "macro_recall"]}, indent=2))


if __name__ == "__main__":
    main()
