from fastapi import APIRouter
from backend.schemas import OrderRequest, OrderResponse
from backend.services.order_service import OrderService
from backend.services.product_service import ProductService

router = APIRouter(prefix="/orders", tags=["orders"])


@router.post("", response_model=OrderResponse)
async def create_order(request: OrderRequest) -> OrderResponse:
    product_service = ProductService()
    order_service = OrderService(product_service)
    return await order_service.create_order(request)
