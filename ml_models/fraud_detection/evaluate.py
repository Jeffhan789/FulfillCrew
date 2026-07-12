"""Evaluate a trained XGBoost fraud detector.

Usage:
    python evaluate.py

Outputs:
    ml_models/fraud_detection/models/evaluation.json
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import auc, precision_recall_curve, roc_auc_score
from xgboost import XGBClassifier

from ml_models.fraud_detection.model import FEATURE_COLUMNS

MODEL_DIR = Path(__file__).parent / "models"
MODEL_PATH = MODEL_DIR / "fraud_xgb.json"
DATA_PATH = MODEL_DIR / "training_data.csv"
EVAL_PATH = MODEL_DIR / "evaluation.json"

THRESHOLD = 0.65


def evaluate() -> None:
    """Load model and test split, compute metrics, and write evaluation.json."""
    if not MODEL_PATH.exists():
        raise FileNotFoundError(f"Model not found at {MODEL_PATH}. Run train.py first.")
    if not DATA_PATH.exists():
        raise FileNotFoundError(f"Data not found at {DATA_PATH}. Run train.py first.")

    df = pd.read_csv(DATA_PATH)
    X = df[FEATURE_COLUMNS].astype(float)
    y = df["is_fraud"].astype(int)

    # Use the same random seed as train.py to reproduce the test split
    from sklearn.model_selection import train_test_split

    _, X_test, _, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    clf = XGBClassifier()
    clf.load_model(str(MODEL_PATH))

    y_prob = clf.predict_proba(X_test)[:, 1]
    y_pred = (y_prob >= THRESHOLD).astype(int)

    roc_auc = roc_auc_score(y_test, y_prob)

    precision_vals, recall_vals, _ = precision_recall_curve(y_test, y_prob)
    pr_auc = auc(recall_vals, precision_vals)

    tp = int(((y_pred == 1) & (y_test == 1)).sum())
    fp = int(((y_pred == 1) & (y_test == 0)).sum())
    fn = int(((y_pred == 0) & (y_test == 1)).sum())
    tn = int(((y_pred == 0) & (y_test == 0)).sum())

    precision_at_threshold = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall_at_threshold = tp / (tp + fn) if (tp + fn) > 0 else 0.0

    results = {
        "threshold": THRESHOLD,
        "roc_auc": round(float(roc_auc), 6),
        "pr_auc": round(float(pr_auc), 6),
        "precision_at_threshold": round(float(precision_at_threshold), 6),
        "recall_at_threshold": round(float(recall_at_threshold), 6),
        "confusion_matrix": {
            "true_positive": tp,
            "false_positive": fp,
            "false_negative": fn,
            "true_negative": tn,
        },
        "model_path": str(MODEL_PATH),
    }

    with EVAL_PATH.open("w", encoding="utf-8") as fh:
        json.dump(results, fh, indent=2)

    print("[evaluate] Evaluation results:")
    for k, v in results.items():
        print(f"    {k}: {v}")


if __name__ == "__main__":
    evaluate()
