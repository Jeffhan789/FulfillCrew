"""Evaluate a trained DemandMLP model on the held-out test set."""

import json
from pathlib import Path
from typing import Dict, List

import numpy as np
import torch
from torch.utils.data import DataLoader

from ml_models.demand_prediction.model import DemandMLP
from ml_models.demand_prediction.train import (
    DemandDataset,
    generate_synthetic_data,
    load_products,
    set_seed,
    TRAIN_SPLIT,
)


MODEL_SAVE_DIR = Path(__file__).parent / "models"
MODEL_SAVE_PATH = MODEL_SAVE_DIR / "demand_mlp.pt"
EVAL_SAVE_PATH = MODEL_SAVE_DIR / "evaluation.json"


def mean_absolute_error(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """MAE."""
    return float(np.mean(np.abs(y_true - y_pred)))


def mean_absolute_percentage_error(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """MAPE in percentage points (0-100 scale)."""
    # Avoid division by zero
    mask = y_true != 0
    if not np.any(mask):
        return 0.0
    return float(np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100)


def r2_score(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Coefficient of determination R²."""
    ss_res = np.sum((y_true - y_pred) ** 2)
    ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
    if ss_tot == 0:
        return 1.0
    return float(1 - ss_res / ss_tot)


def evaluate() -> Dict[str, float]:
    """Load the trained model, run inference on the test split, and report metrics."""
    set_seed()

    if not MODEL_SAVE_PATH.exists():
        raise FileNotFoundError(
            f"Trained model not found at {MODEL_SAVE_PATH}. "
            "Please run train.py first."
        )

    # ------------------------------------------------------------------
    # 1. Recreate the same test data that train.py used
    # ------------------------------------------------------------------
    products = load_products()
    X, y = generate_synthetic_data(products)
    split_idx = int(len(X) * TRAIN_SPLIT)
    X_test, y_test = X[split_idx:], y[split_idx:]

    test_dataset = DemandDataset(X_test, y_test)
    test_loader = DataLoader(test_dataset, batch_size=32, shuffle=False)

    # ------------------------------------------------------------------
    # 2. Load model
    # ------------------------------------------------------------------
    model = DemandMLP(input_dim=9)
    model.load_state_dict(torch.load(MODEL_SAVE_PATH, map_location="cpu"))
    model.eval()

    # ------------------------------------------------------------------
    # 3. Inference
    # ------------------------------------------------------------------
    all_preds: List[float] = []
    all_targets: List[float] = []

    with torch.no_grad():
        for batch_x, batch_y in test_loader:
            preds = model(batch_x)
            all_preds.extend(preds.numpy().tolist())
            all_targets.extend(batch_y.numpy().tolist())

    y_true = np.array(all_targets, dtype=np.float32)
    y_pred = np.array(all_preds, dtype=np.float32)

    # ------------------------------------------------------------------
    # 4. Metrics
    # ------------------------------------------------------------------
    mae = mean_absolute_error(y_true, y_pred)
    mape = mean_absolute_percentage_error(y_true, y_pred)
    r2 = r2_score(y_true, y_pred)

    results = {
        "mae": round(mae, 4),
        "mape_percent": round(mape, 4),
        "r2": round(r2, 4),
        "n_test_samples": int(len(y_true)),
    }

    print("=" * 50)
    print("DemandMLP Evaluation Results")
    print("=" * 50)
    print(f"  MAE  : {mae:.4f}")
    print(f"  MAPE : {mape:.2f}%")
    print(f"  R²   : {r2:.4f}")
    print(f"  N    : {len(y_true)}")
    print("=" * 50)

    # ------------------------------------------------------------------
    # 5. Save to JSON
    # ------------------------------------------------------------------
    MODEL_SAVE_DIR.mkdir(parents=True, exist_ok=True)
    with open(EVAL_SAVE_PATH, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"Evaluation saved to {EVAL_SAVE_PATH}")

    return results


if __name__ == "__main__":
    evaluate()
