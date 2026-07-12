"""Fraud detection model definitions.

Contains the legacy LightweightFraudClassifier heuristic scorer and
feature constants used by the XGBoost training pipeline.
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
