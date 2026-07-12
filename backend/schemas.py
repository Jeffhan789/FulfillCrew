"""Pydantic schemas for API request/response validation."""
from typing import Optional
from pydantic import BaseModel, Field


class Product(BaseModel):
    id: str
    name: str
    price: float
    category: str
    type: str
    quantity: int
    rating: float
    image_link: str


class BasketItem(BaseModel):
    product_id: str
    quantity: int = Field(gt=0)


class OrderRequest(BaseModel):
    user_id: str = "guest"
    items: list[BasketItem] = Field(min_length=1)
    shipping_distance: float = Field(default=12.0, ge=0)
    is_new_user: bool = True


class AgentDecision(BaseModel):
    agent: str
    message: str


class WarehouseBid(BaseModel):
    warehouse_id: str
    bid: float
    workload: int
    distance: float
    stock_level: int
    processing_speed: float
    suitability_score: float
    reason: str


class CourseMapping(BaseModel):
    module: str
    concept: str
    implementation: str
    evidence: list[str]


class ModelEvaluation(BaseModel):
    model_name: str
    course_topic: str
    metric: str
    score: float
    interpretation: str
    training_mode: str
    online_mode: str
    mae: Optional[float] = None
    mape: Optional[float] = None
    r2: Optional[float] = None
    roc_auc: Optional[float] = None
    pr_auc: Optional[float] = None
    shap_explanation: Optional[dict] = None


class OrderResponse(BaseModel):
    order_id: str
    order_status: str
    order_total: float
    selected_warehouse: Optional[str] = None
    risk_score: float
    fraud_status: str
    predicted_demand_next_7_days: int
    restock_recommendation: str
    bids: list[WarehouseBid]
    decision_log: list[AgentDecision]
    course_trace: list[AgentDecision]
    model_evaluations: list[ModelEvaluation]


class HealthCheck(BaseModel):
    status: str
    checks: dict[str, bool | str]


class WebSocketMessage(BaseModel):
    event: str
    order_id: str
    data: dict
