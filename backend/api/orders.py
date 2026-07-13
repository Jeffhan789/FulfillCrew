"""Order API Router — RESTful endpoint for order creation and retrieval.

This is the COMP315 Cloud Computing layer: HTTP API boundary between
frontend (React) and backend (FastAPI). The router delegates all business logic
to OrderService, keeping the API layer thin and stateless.

Design Patterns:
    - Dependency Injection: ProductService is created per-request
    - Thin Controller: API layer only validates input and serialises output
    - Facade: OrderService hides the complexity of 6 cooperating agents

Interview Note:
    Q: Why not put business logic directly in the route handler?
    A: Separation of concerns. The router handles HTTP concerns (status codes,
       headers, serialisation). The service handles domain logic (fraud, inventory,
       bidding). This makes testing easier and allows reusing the service in
       other contexts (e.g., a CLI tool or cron job).
    
    Q: How does Pydantic validation work here?
    A: OrderRequest is a Pydantic BaseModel. FastAPI automatically validates
       the JSON body against the schema, returning 422 if validation fails.
       This eliminates manual validation boilerplate.
"""

from fastapi import APIRouter
from backend.schemas import OrderRequest, OrderResponse
from backend.services.order_service import OrderService
from backend.services.product_service import ProductService

router = APIRouter(prefix="/orders", tags=["orders"])


@router.post("", response_model=OrderResponse)
async def create_order(request: OrderRequest) -> OrderResponse:
    """Create a new order and trigger the full multi-agent fulfillment pipeline.
    
    This is the primary API endpoint. It coordinates 6 agents, persists to
    PostgreSQL, and pushes real-time updates via WebSocket.
    
    Args:
        request: Validated OrderRequest with user_id, items, shipping_distance, is_new_user
        
    Returns:
        OrderResponse with the final order state, agent decisions, and bids.
        
    HTTP Status Codes:
        200 OK: Order processed successfully (even if rejected for stock/fraud)
        422 Unprocessable Entity: Validation error (Pydantic automatic)
        500 Internal Server Error: Unexpected server error (logged with traceback)
    """
    product_service = ProductService()
    order_service = OrderService(product_service)
    return await order_service.create_order(request)
from backend.schemas import OrderRequest, OrderResponse
from backend.services.order_service import OrderService
from backend.services.product_service import ProductService

router = APIRouter(prefix="/orders", tags=["orders"])


@router.post("", response_model=OrderResponse)
async def create_order(request: OrderRequest) -> OrderResponse:
    product_service = ProductService()
    order_service = OrderService(product_service)
    return await order_service.create_order(request)
