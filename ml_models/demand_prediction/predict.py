from ml_models.demand_prediction.model import LightweightDemandMLP

model = LightweightDemandMLP()


def predict_demand(product: dict) -> int:
    category_boost = 1.0 if product.get("category") == "electronics" else 0.4
    features = [
        float(product.get("price", 0)),
        float(product.get("quantity", 0)),
        float(product.get("rating", 0)),
        category_boost,
        1.0 if product.get("type") in {"device", "audio"} else 0.2,
    ]
    return model.predict(features)

