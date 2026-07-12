"""Fraud detection sub-package.

Exports:
    FraudDetector      – XGBoost + SHAP with LightweightFraudClassifier fallback.
    predict_risk       – Legacy compatibility function returning a float score.
    LightweightFraudClassifier – Heuristic logistic scorer.
"""

from ml_models.fraud_detection.model import LightweightFraudClassifier
from ml_models.fraud_detection.predict import FraudDetector, predict_risk

__all__ = [
    "FraudDetector",
    "predict_risk",
    "LightweightFraudClassifier",
]
