import pytest
from backend.database.models import BasketItem, OrderRequest, Product
from backend.services.product_service import ProductService
from backend.services.order_service import OrderService


@pytest.fixture
def sample_products() -> dict[str, Product]:
    return {
        "p-1001": Product(
            id="p-1001",
            name="Wireless Headphones",
            price=59.99,
            category="electronics",
            type="audio",
            quantity=20,
            rating=4.5,
            image_link="https://example.com/headphones.jpg",
        ),
        "p-1002": Product(
            id="p-1002",
            name="Smart Watch",
            price=199.99,
            category="electronics",
            type="device",
            quantity=5,
            rating=4.2,
            image_link="https://example.com/watch.jpg",
        ),
        "p-1003": Product(
            id="p-1003",
            name="Running Shoes",
            price=79.99,
            category="sports",
            type="equipment",
            quantity=0,
            rating=4.0,
            image_link="https://example.com/shoes.jpg",
        ),
    }


@pytest.fixture
def product_service(sample_products: dict[str, Product]) -> ProductService:
    service = ProductService()
    service.products = sample_products
    return service


@pytest.fixture
def order_service(product_service: ProductService) -> OrderService:
    return OrderService(product_service)


@pytest.fixture
def valid_order_request() -> OrderRequest:
    return OrderRequest(
        user_id="test-user",
        items=[BasketItem(product_id="p-1001", quantity=1)],
        shipping_distance=10,
        is_new_user=True,
    )


@pytest.fixture
def out_of_stock_request() -> OrderRequest:
    return OrderRequest(
        user_id="test-user",
        items=[BasketItem(product_id="p-1003", quantity=1)],
        shipping_distance=10,
        is_new_user=False,
    )


@pytest.fixture
def multiple_item_request() -> OrderRequest:
    return OrderRequest(
        user_id="test-user",
        items=[
            BasketItem(product_id="p-1001", quantity=2),
            BasketItem(product_id="p-1002", quantity=1),
        ],
        shipping_distance=18,
        is_new_user=True,
    )
