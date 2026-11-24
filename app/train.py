"""Train the TF-IDF + Logistic Regression pipeline and save model + metrics."""
import json
from datetime import datetime, timezone

import joblib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

from app import config
from app.preprocess import clean_dataframe


def load_training_data():
    """Return (cleaned dataframe, number of correction rows merged in)."""
    base = pd.read_csv(config.DATASET_PATH)[["text", "category"]]
    parts, n_corrections = [base], 0
    if config.CORRECTIONS_PATH.exists():
        corr = pd.read_csv(config.CORRECTIONS_PATH)
        if not corr.empty:
            corr = corr.rename(columns={"correct_category": "category"})[["text", "category"]]
            n_corrections = len(corr)
            parts.append(corr)  # appended last so corrections override duplicates
    df = clean_dataframe(pd.concat(parts, ignore_index=True), keep="last")
    return df, n_corrections


def build_pipeline() -> Pipeline:
    return Pipeline([
        ("tfidf", TfidfVectorizer(ngram_range=(1, 2))),
        ("clf", LogisticRegression(max_iter=1000, C=10)),
    ])


def train_model() -> dict:
    df, n_corrections = load_training_data()
    X, y = df["text"], df["category"]
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    # Score the previous model (if any) on the SAME new test set, for a fair before/after.
    before_accuracy = None
    if config.MODEL_PATH.exists():
        try:
            old = joblib.load(config.MODEL_PATH)
            before_accuracy = float(accuracy_score(y_test, old.predict(X_test)))
        except Exception:
            before_accuracy = None

    pipe = build_pipeline()
    pipe.fit(X_train, y_train)
    y_pred = pipe.predict(X_test)
    labels = sorted(y.unique())

    metrics = {
        "accuracy": float(accuracy_score(y_test, y_pred)),
        "before_accuracy": before_accuracy,
        "labels": labels,
        "classification_report": classification_report(
            y_test, y_pred, labels=labels, output_dict=True, zero_division=0
        ),
        "confusion_matrix": confusion_matrix(y_test, y_pred, labels=labels).tolist(),
        "n_samples": int(len(df)),
        "n_train": int(len(X_train)),
        "n_test": int(len(X_test)),
        "n_corrections_used": int(n_corrections),
        "trained_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }

    config.MODEL_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipe, config.MODEL_PATH)
    config.METRICS_PATH.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    return metrics


if __name__ == "__main__":
    m = train_model()
    print(f"Trained on {m['n_train']} rows, tested on {m['n_test']} rows")
    print(f"Accuracy: {m['accuracy']:.3f}")
