from backend.database.models import BasketItem, OrderRequest, OrderResponse
from backend.services.order_service import OrderService
from backend.services.product_service import ProductService


def test_order_service_returns_agent_decisions(order_service: OrderService) -> None:
    result = order_service.create_order(
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


def test_order_created_with_approved_fraud_status(order_service: OrderService) -> None:
    request = OrderRequest(
        user_id="trusted-user",
        items=[BasketItem(product_id="p-1001", quantity=1)],
        shipping_distance=5,
        is_new_user=False,
    )
    result = order_service.create_order(request)
    assert result.order_status == "created"
    assert result.fraud_status == "approved"
    assert result.risk_score < 0.65


def test_order_review_required_high_risk(order_service: OrderService) -> None:
    request = OrderRequest(
        user_id="new-user",
        items=[BasketItem(product_id="p-1002", quantity=5)],
        shipping_distance=50,
        is_new_user=True,
    )
    result = order_service.create_order(request)
    assert result.fraud_status == "review_required"
    assert result.risk_score >= 0.65


def test_order_rejected_out_of_stock(
    order_service: OrderService, out_of_stock_request: OrderRequest
) -> None:
    result = order_service.create_order(out_of_stock_request)
    assert result.order_status == "rejected_out_of_stock"
    assert result.selected_warehouse is None
    assert len(result.bids) == 0


def test_multiple_items_order(order_service: OrderService, multiple_item_request: OrderRequest) -> None:
    result = order_service.create_order(multiple_item_request)
    assert result.order_total == round(59.99 * 2 + 199.99 * 1, 2)
    assert result.order_status in {"created", "review_required"}
    assert len(result.bids) == 3


def test_inventory_reservation_for_approved_order(order_service: OrderService, valid_order_request: OrderRequest) -> None:
    initial_stock = order_service.product_service.products["p-1001"].quantity
    result = order_service.create_order(valid_order_request)
    if result.order_status == "created":
        assert order_service.product_service.products["p-1001"].quantity == initial_stock - 1


def test_warehouse_bids_structure(order_service: OrderService, valid_order_request: OrderRequest) -> None:
    result = order_service.create_order(valid_order_request)
    for bid in result.bids:
        assert bid.warehouse_id
        assert bid.bid > 0
        assert bid.suitability_score > 0
        assert bid.reason


def test_course_trace_present(order_service: OrderService, valid_order_request: OrderRequest) -> None:
    result = order_service.create_order(valid_order_request)
    assert len(result.course_trace) == 3
    modules = [entry.agent for entry in result.course_trace]
    assert "COMP315 Cloud Computing" in modules
    assert "COMP310 Multi-Agent Systems" in modules
    assert "ELEC320 Neural Networks" in modules


def test_model_evaluations_present(order_service: OrderService, valid_order_request: OrderRequest) -> None:
    result = order_service.create_order(valid_order_request)
    assert len(result.model_evaluations) == 2
    model_names = [m.model_name for m in result.model_evaluations]
    assert "Demand Prediction MLP Interface" in model_names
    assert "Fraud Detection Classifier Interface" in model_names


def test_restock_recommendation_logic(order_service: OrderService) -> None:
    request = OrderRequest(
        user_id="test-user",
        items=[BasketItem(product_id="p-1001", quantity=1)],
        shipping_distance=10,
        is_new_user=False,
    )
    result = order_service.create_order(request)
    assert result.restock_recommendation in {"restock recommended", "no restock needed"}
