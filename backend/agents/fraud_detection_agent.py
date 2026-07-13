"""Fraud Detection Agent — bridges ML inference (ELEC320) with MAS (COMP310).

This agent demonstrates how machine learning models are deployed as
microservices (or "model-as-a-service") within a multi-agent architecture.

The inference pipeline:
1. Extract order features (total, item count, price, user history, distance)
2. Call the trained XGBoost model via predict_risk()
3. Compare risk score against threshold (0.65)
4. Return status: "approved" or "review_required"

Model Architecture (ELEC320):
    - XGBoost: Gradient-boosted decision trees for tabular fraud detection
    - SHAP: Explainability — tells the user WHY an order was flagged
    - Fallback: LightweightFraudClassifier (heuristic logistic regression) if
      no trained model is on disk.

Interview Note:
    Q: Why 0.65 as the threshold?
    A: It's a business decision balancing precision and recall. In a real
       system you would tune this on a validation set using ROC-AUC analysis.
       
    Q: How would you handle concept drift in fraud patterns?
    A: Retrain the model on recent labelled data, use an online learning
       framework, or deploy a challenger model alongside the current one
       and monitor performance degradation via A/B testing.
"""

from backend.agents.base_agent import BaseAgent
from ml_models.fraud_detection.predict import predict_risk


class FraudDetectionAgent(BaseAgent):
    """ML-powered fraud detection agent.
    
    Architecture Pattern: ML Model-as-a-Service
    The agent wraps the predict_risk() function, which internally uses
    XGBoost if available or falls back to a heuristic scorer. This ensures
    the system is functional even before any model training has occurred.
    """
    name = "Fraud Detection Agent"

    # Threshold tuned to balance false positives and false negatives.
    # In production this would be configurable via environment variables.
    THRESHOLD = 0.65

    def score(self, features: dict) -> tuple[float, str]:
        """Score an order for fraud risk.
        
        Args:
            features: Dictionary of order features matching the model's
                FEATURE_COLUMNS (see ml_models/fraud_detection/model.py).
                
        Returns:
            (risk_score, status) where status is "approved" or "review_required".
            
        Interview Note:
            Q: What features are most important for fraud detection?
            A: SHAP analysis (from evaluate.py) shows that order_total,
               is_new_user, and orders_in_last_hour are typically the top
               contributors. See ml_models/fraud_detection/README.md for
               the full SHAP report.
        """
        risk_score = predict_risk(features)
        status = "review_required" if risk_score >= self.THRESHOLD else "approved"
        return risk_score, status

