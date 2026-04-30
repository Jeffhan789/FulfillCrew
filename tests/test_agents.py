from backend.database.models import BasketItem, OrderRequest
from backend.services.order_service import OrderService
from backend.services.product_service import ProductService


def test_order_service_returns_agent_decisions():
    service = OrderService(ProductService())
    result = service.create_order(
        OrderRequest(
            user_id="test-user",
            items=[BasketItem(product_id="p-1001", quantity=1)],
            shipping_distance=10,
            is_new_user=True,
        )
    )

    assert result.order_status in {"created", "review_required"}
    assert result.selected_warehouse is not None
    assert len(result.decision_log) >= 5
    assert len(result.course_trace) == 3
    assert len(result.model_evaluations) == 2
    assert result.bids[0].reason
