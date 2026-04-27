from backend.agents.base_agent import BaseAgent
from backend.database.models import Product
from ml_models.demand_prediction.predict import predict_demand


class DemandPredictionAgent(BaseAgent):
    name = "Demand Prediction Agent"

    def predict(self, products: list[Product]) -> int:
        return sum(predict_demand(product.model_dump()) for product in products)

