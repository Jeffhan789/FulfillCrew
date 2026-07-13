"""Inference entry point for the demand prediction model (PyTorch MLP).

This module demonstrates the complete ML inference pipeline:
1. Feature encoding (raw product dict → 9-dim numpy vector)
2. Model loading (lazy singleton pattern — load once, reuse many times)
3. Forward pass (torch.no_grad() for inference efficiency)
4. Post-processing (round, clamp to non-negative)

Graceful Degradation:
    If the trained .pt model is missing, the system falls back to a heuristic
    function that mirrors the original LightweightDemandMLP logic. This ensures
    the e-commerce system is functional even before any model training.

Model Persistence:
    - PyTorch state_dict format (.pt file) stores only learnable weights
    - Load with map_location="cpu" to ensure GPU-trained models work on CPU-only hosts
    - model.eval() disables Dropout and sets batch norm to inference mode

Interview Note:
    Q: Why use torch.no_grad() during inference?
    A: It disables gradient computation, reducing memory usage and speeding up
       forward passes. Gradients are only needed during backpropagation (training).
       
    Q: What is the lazy singleton pattern used here?
    A: predict_demand._model is set on first successful call and reused for
       all subsequent calls. This avoids reloading the model from disk on every
       prediction, which would be I/O-bound and slow.
       
    Q: Why np.float32 instead of np.float64?
    A: GPUs and neural networks typically use 32-bit floats. Using float64
       would double memory usage without improving model accuracy for this task.
       
    Q: How would you improve prediction latency for high-traffic scenarios?
    A: 1. Batch predictions (predict_batch) instead of one-by-one
       2. ONNX export for optimised CPU inference
       3. Redis caching for frequently requested products
       4. GPU inference if latency is critical and batch size is large
"""

import math
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import torch

from ml_models.demand_prediction.model import DemandMLP


MODEL_PATH = Path(__file__).parent / "models" / "demand_mlp.pt"

CATEGORY_MAP = {
    "electronics": 1.0,
    "home": 0.5,
}

TYPE_MAP = {
    "device": 1.0,
    "audio": 0.8,
    "lighting": 0.6,
}


def _encode_features(product_features: Dict[str, Any]) -> np.ndarray:
    """Convert a raw product dict into the 9-dimensional model input vector.

    Expected keys (with sensible defaults):
        - price, rating, category, type, quantity
        - day_of_week, month, is_weekend, sales_last_7_days, sales_last_30_days

    Missing optional keys are filled with heuristic defaults so the model
    can still produce a prediction.
    """
    price = float(product_features.get("price", 50.0))
    rating = float(product_features.get("rating", 3.0))
    category = str(product_features.get("category", "home")).lower()
    type_ = str(product_features.get("type", "device")).lower()
    category_enc = CATEGORY_MAP.get(category, 0.5)
    type_enc = TYPE_MAP.get(type_, 0.6)

    # Temporal defaults: assume mid-week, mid-year, weekday
    day_of_week = float(product_features.get("day_of_week", 2.0))
    month = float(product_features.get("month", 6.0))
    is_weekend = float(product_features.get("is_weekend", 0.0))

    # Historical sales defaults: derive from quantity if absent
    quantity = float(product_features.get("quantity", 10.0))
    sales_last_7 = float(product_features.get("sales_last_7_days", quantity * 0.7))
    sales_last_30 = float(product_features.get("sales_last_30_days", quantity * 3.0))

    vec = np.array(
        [
            price,
            rating,
            category_enc,
            type_enc,
            day_of_week,
            month,
            is_weekend,
            sales_last_7,
            sales_last_30,
        ],
        dtype=np.float32,
    )
    return vec


def _heuristic_fallback(product_features: Dict[str, Any]) -> int:
    """Deterministic fallback used when no trained model is on disk.

    Mirrors the original LightweightDemandMLP logic for backward compatibility.
    """
    category_boost = 1.0 if product_features.get("category") == "electronics" else 0.4
    features = [
        float(product_features.get("price", 0)),
        float(product_features.get("quantity", 0)),
        float(product_features.get("rating", 0)),
        category_boost,
        1.0 if product_features.get("type") in {"device", "audio"} else 0.2,
    ]
    weights = [0.018, -0.025, 0.75, 0.32, 0.2]
    bias = 2.5
    activation = bias + sum(w * v for w, v in zip(weights, features))
    hidden = max(0.0, activation)
    output = 1 + 6 / (1 + math.exp(-hidden / 4))
    return max(1, int(round(output)))


def load_model(model_path: Optional[str] = None) -> DemandMLP:
    """Load a trained DemandMLP from disk.

    Args:
        model_path: Optional explicit path to the .pt file.  Defaults to the
            ``models/demand_mlp.pt`` sibling of this module.

    Returns:
        An evaluated ``DemandMLP`` instance on CPU.
    """
    path = Path(model_path) if model_path else MODEL_PATH
    model = DemandMLP(input_dim=9)
    model.load_state_dict(torch.load(path, map_location="cpu"))
    model.eval()
    return model


def predict_demand(product_features: Dict[str, Any]) -> int:
    """Return predicted next 7-day sales as an integer.

    If a trained model exists on disk it is loaded and used; otherwise a
    heuristic fallback is returned so callers never crash.
    """
    if not MODEL_PATH.exists():
        return _heuristic_fallback(product_features)

    # Lazy-load model on first successful call (kept in module namespace for reuse)
    if not hasattr(predict_demand, "_model"):
        predict_demand._model = load_model(MODEL_PATH)  # type: ignore[attr-defined]

    model: DemandMLP = predict_demand._model  # type: ignore[attr-defined]
    vec = _encode_features(product_features)
    tensor = torch.from_numpy(vec).unsqueeze(0)  # (1, 9)

    with torch.no_grad():
        pred = model(tensor).item()

    return max(0, int(round(pred)))


def predict_batch(products: List[Dict[str, Any]]) -> List[int]:
    """Batch prediction for multiple products.

    Returns a list of integer predictions in the same order as the input.
    """
    if not products:
        return []

    if not MODEL_PATH.exists():
        return [_heuristic_fallback(p) for p in products]

    if not hasattr(predict_batch, "_model"):
        predict_batch._model = load_model(MODEL_PATH)  # type: ignore[attr-defined]

    model: DemandMLP = predict_batch._model  # type: ignore[attr-defined]
    matrix = np.stack([_encode_features(p) for p in products], axis=0)  # (N, 9)
    tensor = torch.from_numpy(matrix)

    with torch.no_grad():
        preds = model(tensor).numpy()

    return [max(0, int(round(p))) for p in preds.tolist()]
