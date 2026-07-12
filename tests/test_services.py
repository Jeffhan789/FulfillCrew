from backend.services.product_service import ProductService
from backend.services.order_service import OrderService
from backend.database.models import BasketItem, OrderRequest


def test_product_service_loads_products() -> None:
    service = ProductService()
    products = service.list_products()
    assert isinstance(products, list)
    assert len(products) > 0
    for product in products:
        assert product.id
        assert product.price > 0
        assert product.quantity >= 0


def test_product_service_get_product_map() -> None:
    service = ProductService()
    product_map = service.get_product_map()
    assert isinstance(product_map, dict)
    assert "p-1001" in product_map


def test_order_service_init(product_service: ProductService) -> None:
    order_service = OrderService(product_service)
    assert order_service.order_agent is not None
    assert order_service.inventory_agent is not None
    assert order_service.coordinator_agent is not None
    assert order_service.demand_agent is not None
    assert order_service.fraud_agent is not None


def test_order_total_calculation(order_service: OrderService) -> None:
    request = OrderRequest(
        user_id="test-user",
        items=[
            BasketItem(product_id="p-1001", quantity=2),
            BasketItem(product_id="p-1002", quantity=1),
        ],
        shipping_distance=10,
        is_new_user=False,
    )
    result = order_service.create_order(request)
    expected = round(59.99 * 2 + 199.99 * 1, 2)
    assert result.order_total == expected


def test_order_with_unknown_product_rejected(order_service: OrderService) -> None:
    request = OrderRequest(
        user_id="test-user",
        items=[BasketItem(product_id="p-unknown", quantity=1)],
        shipping_distance=10,
        is_new_user=False,
    )
    result = order_service.create_order(request)
    assert result.order_status == "rejected_out_of_stock"


def test_order_uuid_generated(order_service: OrderService) -> None:
    request = OrderRequest(
        user_id="test-user",
        items=[BasketItem(product_id="p-1001", quantity=1)],
        shipping_distance=10,
        is_new_user=False,
    )
    result = order_service.create_order(request)
    assert result.order_id
    assert len(result.order_id) == 36


def test_demand_prediction_positive(order_service: OrderService) -> None:
    request = OrderRequest(
        user_id="test-user",
        items=[BasketItem(product_id="p-1001", quantity=1)],
        shipping_distance=10,
        is_new_user=False,
    )
    result = order_service.create_order(request)
    assert result.predicted_demand_next_7_days > 0


def test_inventory_reservation_reduces_stock(order_service: OrderService) -> None:
    initial_stock = order_service.product_service.products["p-1001"].quantity
    request = OrderRequest(
        user_id="test-user",
        items=[BasketItem(product_id="p-1001", quantity=1)],
        shipping_distance=5,
        is_new_user=False,
    )
    result = order_service.create_order(request)
    if result.order_status == "created":
        assert order_service.product_service.products["p-1001"].quantity == initial_stock - 1


def test_model_evaluations_fields(order_service: OrderService) -> None:
    request = OrderRequest(
        user_id="test-user",
        items=[BasketItem(product_id="p-1001", quantity=1)],
        shipping_distance=10,
        is_new_user=False,
    )
    result = order_service.create_order(request)
    for evaluation in result.model_evaluations:
        assert evaluation.model_name
        assert evaluation.course_topic
        assert evaluation.metric
        assert evaluation.interpretation
        assert evaluation.training_mode
        assert evaluation.online_mode


def test_decision_log_contains_agent_names(order_service: OrderService) -> None:
    request = OrderRequest(
        user_id="test-user",
        items=[BasketItem(product_id="p-1001", quantity=1)],
        shipping_distance=10,
        is_new_user=False,
    )
    result = order_service.create_order(request)
    agent_names = [entry.agent for entry in result.decision_log]
    assert "Order Agent" in agent_names
    assert "Fraud Detection Agent" in agent_names
    assert "Inventory Agent" in agent_names
    assert "Coordinator Agent" in agent_names
