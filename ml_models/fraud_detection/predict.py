from ml_models.fraud_detection.model import LightweightFraudClassifier

model = LightweightFraudClassifier()


def predict_risk(features: dict) -> float:
    return model.predict_proba(features)

