"""Synthetic data generation and XGBoost training for fraud detection.

Usage:
    python train.py

Outputs:
    ml_models/fraud_detection/models/fraud_xgb.json
    ml_models/fraud_detection/models/training_data.csv
"""

from __future__ import annotations

import json
import random
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from xgboost import XGBClassifier

from ml_models.fraud_detection.model import FEATURE_COLUMNS

SEED = 42
random.seed(SEED)
np.random.seed(SEED)

N_SAMPLES = 5500
FRAUD_RATE = 0.01
FRAUD_LABEL = 1
NORMAL_LABEL = 0

MODEL_DIR = Path(__file__).parent / "models"
MODEL_PATH = MODEL_DIR / "fraud_xgb.json"
DATA_PATH = MODEL_DIR / "training_data.csv"
META_PATH = MODEL_DIR / "training_meta.json"

XGB_PARAMS = {
    "max_depth": 5,
    "learning_rate": 0.1,
    "n_estimators": 200,
    "scale_pos_weight": 99,  # ~99 % normal vs 1 % fraud
    "use_label_encoder": False,
    "eval_metric": "logloss",
    "random_state": SEED,
    "n_jobs": 4,
}


def _generate_normal_row() -> dict[str, float | int]:
    """Generate a single legitimate order record."""
    order_total = round(np.random.normal(loc=120.0, scale=60.0), 2)
    order_total = max(10.0, order_total)
    number_of_items = int(np.random.poisson(lam=3) + 1)
    average_item_price = round(order_total / max(number_of_items, 1), 2)
    is_new_user = 0
    account_age_days = int(np.random.exponential(scale=180) + 30)
    shipping_distance = round(np.random.normal(loc=25.0, scale=15.0), 2)
    shipping_distance = max(1.0, shipping_distance)
    billing_shipping_match = 1
    order_hour = random.randint(6, 22)
    is_night_order = 0
    orders_in_last_hour = int(np.random.poisson(lam=0.5))
    return {
        "order_total": order_total,
        "number_of_items": number_of_items,
        "average_item_price": average_item_price,
        "is_new_user": is_new_user,
        "account_age_days": account_age_days,
        "shipping_distance": shipping_distance,
        "billing_shipping_match": billing_shipping_match,
        "order_hour": order_hour,
        "is_night_order": is_night_order,
        "orders_in_last_hour": orders_in_last_hour,
    }


def _generate_fraud_row() -> dict[str, float | int]:
    """Generate a single fraudulent order record.

    Fraud patterns modelled:
        - High order total (luxury / bulk fraud)
        - Abnormally large shipping distance
        - New user with rapid successive orders
        - Night-time orders (higher bot/script probability)
        - Billing/shipping mismatch
    """
    # Pick a dominant fraud pattern
    pattern = random.choice(["high_total", "long_distance", "new_user_burst", "night_mismatch"])

    order_total = round(np.random.normal(loc=120.0, scale=60.0), 2)
    number_of_items = int(np.random.poisson(lam=3) + 1)
    average_item_price = round(order_total / max(number_of_items, 1), 2)
    is_new_user = 0
    account_age_days = int(np.random.exponential(scale=180) + 30)
    shipping_distance = round(np.random.normal(loc=25.0, scale=15.0), 2)
    shipping_distance = max(1.0, shipping_distance)
    billing_shipping_match = 1
    order_hour = random.randint(6, 22)
    is_night_order = 0
    orders_in_last_hour = int(np.random.poisson(lam=0.5))

    if pattern == "high_total":
        order_total = round(np.random.uniform(800, 5000), 2)
        number_of_items = int(np.random.uniform(1, 20))
        average_item_price = round(order_total / max(number_of_items, 1), 2)
    elif pattern == "long_distance":
        shipping_distance = round(np.random.uniform(300, 2000), 2)
        order_total = round(np.random.uniform(300, 1500), 2)
    elif pattern == "new_user_burst":
        is_new_user = 1
        account_age_days = int(np.random.uniform(0, 7))
        orders_in_last_hour = int(np.random.uniform(3, 15))
        order_total = round(np.random.uniform(200, 1200), 2)
    elif pattern == "night_mismatch":
        order_hour = random.choice([0, 1, 2, 3, 4, 5, 23])
        is_night_order = 1
        billing_shipping_match = 0
        order_total = round(np.random.uniform(400, 3000), 2)

    return {
        "order_total": order_total,
        "number_of_items": number_of_items,
        "average_item_price": average_item_price,
        "is_new_user": is_new_user,
        "account_age_days": account_age_days,
        "shipping_distance": shipping_distance,
        "billing_shipping_match": billing_shipping_match,
        "order_hour": order_hour,
        "is_night_order": is_night_order,
        "orders_in_last_hour": orders_in_last_hour,
    }


def generate_synthetic_data(n_samples: int = N_SAMPLES, fraud_rate: float = FRAUD_RATE) -> pd.DataFrame:
    """Create a balanced-ish synthetic dataset with realistic fraud signals."""
    n_fraud = max(1, int(n_samples * fraud_rate))
    n_normal = n_samples - n_fraud

    rows: list[dict[str, float | int]] = []
    for _ in range(n_normal):
        row = _generate_normal_row()
        row["is_fraud"] = NORMAL_LABEL
        rows.append(row)
    for _ in range(n_fraud):
        row = _generate_fraud_row()
        row["is_fraud"] = FRAUD_LABEL
        rows.append(row)

    df = pd.DataFrame(rows)
    df = df.sample(frac=1, random_state=SEED).reset_index(drop=True)
    return df


def train() -> None:
    """Generate data, train XGBoost, and persist artifacts."""
    print("[train] Generating synthetic data …")
    df = generate_synthetic_data()
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    df.to_csv(DATA_PATH, index=False)
    print(f"[train] Saved {len(df)} rows to {DATA_PATH}")

    X = df[FEATURE_COLUMNS].astype(float)
    y = df["is_fraud"].astype(int)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=SEED, stratify=y
    )
    print(f"[train] Train size: {len(X_train)} | Test size: {len(X_test)}")

    clf = XGBClassifier(**XGB_PARAMS)
    clf.fit(X_train, y_train)
    clf.save_model(str(MODEL_PATH))
    print(f"[train] Model saved to {MODEL_PATH}")

    meta = {
        "feature_columns": FEATURE_COLUMNS,
        "n_samples": len(df),
        "n_fraud": int(y.sum()),
        "n_normal": int((y == 0).sum()),
        "train_size": len(X_train),
        "test_size": len(X_test),
        "xgb_params": {k: v for k, v in XGB_PARAMS.items() if k not in ("use_label_encoder", "eval_metric")},
    }
    with META_PATH.open("w", encoding="utf-8") as fh:
        json.dump(meta, fh, indent=2)
    print(f"[train] Meta saved to {META_PATH}")


if __name__ == "__main__":
    train()
