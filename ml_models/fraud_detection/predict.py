"""Inference entry point for fraud detection with XGBoost + SHAP.

Provides both a modern FraudDetector class and a legacy predict_risk()
compatibility function used by FraudDetectionAgent.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import shap
import xgboost as xgb

from ml_models.fraud_detection.model import FEATURE_COLUMNS, LightweightFraudClassifier

DEFAULT_MODEL_PATH = Path(__file__).parent / "models" / "fraud_xgb.json"
THRESHOLD = 0.65


class FraudDetector:
    """Trained XGBoost fraud detector with SHAP explainability.

    Falls back to LightweightFraudClassifier if the XGBoost model file is absent.
    """

    def __init__(self, model_path: str | None = None) -> None:
        """Initialise detector.

        Args:
            model_path: Path to a saved XGBoost JSON model. If None, uses the
                default artifact location inside this package.
        """
        if model_path is None:
            model_path = DEFAULT_MODEL_PATH
        self._model_path = Path(model_path)

        if self._model_path.exists():
            self.model: Any = xgb.XGBClassifier()
            self.model.load_model(str(self._model_path))
            self.explainer = shap.TreeExplainer(self.model)
            self._is_xgb = True
        else:
            # Fallback heuristic scorer
            self.model = LightweightFraudClassifier()
            self.explainer = None
            self._is_xgb = False

    def _to_array(self, order_features: dict[str, Any]) -> np.ndarray:
        """Convert a feature dict into a NumPy array aligned with FEATURE_COLUMNS."""
        return np.array(
            [[float(order_features.get(col, 0.0)) for col in FEATURE_COLUMNS]],
            dtype=float,
        )

    def score(
        self, order_features: dict[str, Any]
    ) -> tuple[float, str, dict[str, float]]:
        """Score an order and return risk, decision, and SHAP explanation.

        Args:
            order_features: Dictionary of order attributes.

        Returns:
            A 3-tuple of (risk_score, decision, shap_explanation).
            * risk_score — float in [0.0, 1.0].
            * decision — "approved" or "review_required".
            * shap_explanation — mapping feature_name -> contribution value.
              Empty dict when running in fallback mode.
        """
        if self._is_xgb:
            X = self._to_array(order_features)
            risk_score = float(self.model.predict_proba(X)[0, 1])
            risk_score = round(max(0.0, min(1.0, risk_score)), 6)

            if self.explainer is not None:
                shap_values = self.explainer.shap_values(X)
                # TreeExplainer.shap_values returns a list [normal, fraud] for binary
                if isinstance(shap_values, list):
                    fraud_shap = shap_values[1][0]
                else:
                    fraud_shap = shap_values[0]
                shap_explanation = {
                    col: round(float(val), 6)
                    for col, val in zip(FEATURE_COLUMNS, fraud_shap)
                }
            else:
                shap_explanation = {}
        else:
            risk_score = self.model.predict_proba(order_features)
            risk_score = round(max(0.0, min(1.0, risk_score)), 6)
            shap_explanation = {}

        decision = "review_required" if risk_score >= THRESHOLD else "approved"
        return risk_score, decision, shap_explanation

    def predict(self, order_features: dict[str, Any]) -> int:
        """Return binary prediction (1 = fraud, 0 = normal)."""
        score, _, _ = self.score(order_features)
        return 1 if score >= THRESHOLD else 0


def predict_risk(features: dict[str, Any]) -> float:
    """Legacy compatibility function used by FraudDetectionAgent.

    Returns the risk score only; for full explainability use FraudDetector.score().
    """
    detector = FraudDetector()
    risk_score, _, _ = detector.score(features)
    return risk_score
