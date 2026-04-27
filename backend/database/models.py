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
    items: list[BasketItem]
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


class OrderResponse(BaseModel):
    order_id: str
    order_status: str
    order_total: float
    selected_warehouse: str | None
    risk_score: float
    fraud_status: str
    predicted_demand_next_7_days: int
    restock_recommendation: str
    bids: list[WarehouseBid]
    decision_log: list[AgentDecision]

