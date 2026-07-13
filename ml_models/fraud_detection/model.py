"""Fraud detection model definitions (ELEC320 Neural Networks).

This module contains two scorers:
1. LightweightFraudClassifier — heuristic logistic-style fallback (no ML training needed)
2. FEATURE_COLUMNS — schema definition for the XGBoost training pipeline

Mathematical Foundation:
    The fallback uses a logistic function: p = 1 / (1 + e^(-logit))
    where logit = w0 + w1*x1 + w2*x2 + ... + wn*xn
    
    This is essentially a single-layer neural network (perceptron) with
    sigmoid activation — the simplest form of binary classification.

XGBoost Integration (see predict.py):
    When a trained model exists on disk (fraud_xgb.json), the system uses
    XGBoost instead of this heuristic. XGBoost is a gradient-boosted ensemble
    of decision trees, which typically outperforms logistic regression on
    tabular data with non-linear interactions.

SHAP Explainability (see predict.py):
    SHAP (SHapley Additive exPlanations) decomposes the model prediction
    into contributions from each feature. This answers "why was this order
    flagged?" — critical for regulatory compliance and user trust.

Interview Note:
    Q: Why 0.65 as the threshold?
    A: It balances precision (minimising false alarms) and recall (catching
       real fraud). In practice, you'd tune this using a ROC curve and
       considering the business cost of false positives vs false negatives.
       
    Q: How is XGBoost different from a neural network?
    A: XGBoost builds an ensemble of decision trees sequentially, where each
       tree corrects errors of the previous ones. It's excellent for tabular
       data with mixed feature types. Neural networks learn distributed
       representations and excel at unstructured data (images, text).
"""

import math
from typing import Any

# Feature column order expected by the XGBoost pipeline.
FEATURE_COLUMNS: list[str] = [
    "order_total",
    "number_of_items",
    "average_item_price",
    "is_new_user",
    "account_age_days",
    "shipping_distance",
    "billing_shipping_match",
    "order_hour",
    "is_night_order",
    "orders_in_last_hour",
]


class LightweightFraudClassifier:
    """Heuristic logistic-style scorer used as fallback when no trained model exists."""

    def predict_proba(self, features: dict[str, Any]) -> float:
        """Return a risk score in [0, 1] based on hard-coded weights."""
        order_total = float(features.get("order_total", 0))
        number_of_items = float(features.get("number_of_items", 0))
        average_item_price = float(features.get("average_item_price", 0))
        is_new_user = 1.0 if features.get("is_new_user") else 0.0
        shipping_distance = float(features.get("shipping_distance", 0))

        logit = (
            -3.4
            + 0.004 * order_total
            + 0.08 * number_of_items
            + 0.003 * average_item_price
            + 0.75 * is_new_user
            + 0.006 * shipping_distance
        )
        return round(1 / (1 + math.exp(-logit)), 3)

    def predict(self, features: dict[str, Any]) -> int:
        """Return binary prediction: 1 = fraud, 0 = normal."""
        return 1 if self.predict_proba(features) >= 0.65 else 0
