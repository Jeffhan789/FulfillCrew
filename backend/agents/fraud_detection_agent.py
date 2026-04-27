from backend.agents.base_agent import BaseAgent
from ml_models.fraud_detection.predict import predict_risk


class FraudDetectionAgent(BaseAgent):
    name = "Fraud Detection Agent"

    def score(self, features: dict) -> tuple[float, str]:
        risk_score = predict_risk(features)
        status = "review_required" if risk_score >= 0.65 else "approved"
        return risk_score, status

