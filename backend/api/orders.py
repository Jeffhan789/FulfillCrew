from fastapi import APIRouter

from backend.database.db import product_service
from backend.database.models import OrderRequest, OrderResponse
from backend.services.order_service import OrderService

router = APIRouter(prefix="/orders", tags=["orders"])
order_service = OrderService(product_service)


@router.post("", response_model=OrderResponse)
def create_order(request: OrderRequest) -> OrderResponse:
    return order_service.create_order(request)

