"""Inference entry point for fraud detection with XGBoost + SHAP.

Provides both a modern FraudDetector class and a legacy predict_risk()
compatibility function used by FraudDetectionAgent.
"""

"""Inference entry point for fraud detection with XGBoost + SHAP.

This module demonstrates:
1. Model loading: XGBoost JSON format (interoperable, human-readable)
2. SHAP explainability: TreeExplainer for feature attribution
3. Graceful fallback: heuristic scorer when trained model is unavailable
4. Compatibility layer: predict_risk() for legacy agent integration

XGBoost + SHAP Architecture (ELEC320):
    XGBoost: Ensemble of gradient-boosted decision trees
    - Handles non-linear feature interactions automatically
    - Robust to outliers and missing values
    - Fast inference (tree traversal is O(depth))
    
    SHAP: Game-theoretic feature attribution
    - Based on Shapley values from cooperative game theory
    - Tells us HOW MUCH each feature contributed to the fraud score
    - Enables regulatory compliance ("right to explanation")

Model Format:
    - XGBoost saves as JSON (self-contained, no Python pickling)
    - Load with xgb.XGBClassifier().load_model()
    - TreeExplainer requires the trained model object

Interview Note:
    Q: Why SHAP instead of feature importance?
    A: Feature importance (gain/weight) only tells us which features are
       globally important. SHAP tells us the contribution of EACH feature
       for EACH individual prediction, enabling personalised explanations.
       
    Q: What happens if the XGBoost model is corrupted?
    A: The try/except in FraudDetector.__init__ would fail, and we'd fall
       back to LightweightFraudClassifier. In production you'd add model
       checksum validation and A/B testing between model versions.
       
    Q: How do you handle model drift over time?
    A: Monitor ROC-AUC on a held-out validation set. When it drops below
       a threshold, trigger a retraining pipeline. Prometheus metrics
       (fraud_roc_auc) expose this for alerting.
"""

from pathlib import Path
from typing import Any

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
            try:
                import shap
                import xgboost as xgb

                self.model: Any = xgb.XGBClassifier()
                self.model.load_model(str(self._model_path))
                self.explainer = shap.TreeExplainer(self.model)
                self._is_xgb = True
            except (ImportError, OSError, ValueError):
                self.model = LightweightFraudClassifier()
                self.explainer = None
                self._is_xgb = False
        else:
            # Fallback heuristic scorer
            self.model = LightweightFraudClassifier()
            self.explainer = None
            self._is_xgb = False

    def _to_array(self, order_features: dict[str, Any]) -> Any:
        """Convert a feature dict into a NumPy array aligned with FEATURE_COLUMNS."""
        import numpy as np

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
