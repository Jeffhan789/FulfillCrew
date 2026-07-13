"""Demand Prediction Agent — MLP-based demand forecasting (ELEC320 Neural Networks).

This agent wraps a PyTorch Multi-Layer Perceptron (MLP) that predicts
next 7-day sales for each product. The predictions are aggregated across
the order basket to generate a restock recommendation.

MLP Architecture (see ml_models/demand_prediction/model.py):
    Input: 9-dim feature vector
        ┌────────────────────────────────────────────┐
        │ price, rating, category_enc, type_enc,     │
        │ day_of_week, month, is_weekend,            │
        │ sales_last_7_days, sales_last_30_days      │
        └────────────────────────────────────────────┘
                  ↓
    Layer 1: Linear(9 → 64) + ReLU + Dropout(0.2)
                  ↓
    Layer 2: Linear(64 → 32) + ReLU + Dropout(0.2)
                  ↓
    Output: Linear(32 → 1)  [scalar regression]

Interview Note:
    Q: Why MLP instead of LSTM/Transformer for demand prediction?
    A: MLP is simpler, faster to train, and works well with tabular features.
       For true time-series forecasting we would use LSTM or Prophet, but
       the ELEC320 course focuses on neural network fundamentals (MLP, backprop).
       
    Q: How do you handle cold-start products with no sales history?
    A: The _encode_features() function in predict.py provides sensible defaults
       (e.g., sales_last_7_days = quantity * 0.7) so the model can still
       produce a prediction even without historical data.
"""

from backend.agents.base_agent import BaseAgent
from backend.schemas import Product
from ml_models.demand_prediction.predict import predict_demand


class DemandPredictionAgent(BaseAgent):
    """Predicts future demand using a trained PyTorch MLP.
    
    The prediction is used to decide whether to recommend restocking:
    - If predicted_demand > current_stock: recommend restock
    - Otherwise: no action needed
    
    This demonstrates how ML models can be embedded into business workflows
    rather than operating as standalone prediction services.
    """
    name = "Demand Prediction Agent"

    def predict(self, products: list[Product]) -> int:
        """Predict total demand for the next 7 days across all products.
        
        Args:
            products: List of Product objects from the order basket.
            
        Returns:
            Integer sum of predicted demand for each product.
            
        Interview Note:
            Q: Why sum individual predictions instead of predicting basket-level demand?
            A: Basket-level demand is harder to model due to sparse combinations.
               Product-level predictions are more generalisable and can be cached
               per product. Aggregation is trivially parallelisable.
        """
        return sum(predict_demand(product.model_dump()) for product in products)
