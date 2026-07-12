import pytest
from fastapi.testclient import TestClient
from backend.main import app


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def test_health_check(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_list_products(client: TestClient) -> None:
    response = client.get("/products")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    product = data[0]
    assert "id" in product
    assert "name" in product
    assert "price" in product
    assert "category" in product
    assert "quantity" in product


def test_create_order_success(client: TestClient) -> None:
    payload = {
        "user_id": "test-user",
        "items": [{"product_id": "p-1001", "quantity": 1}],
        "shipping_distance": 10,
        "is_new_user": False,
    }
    response = client.post("/orders", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "order_id" in data
    assert data["order_status"] in {"created", "review_required"}
    assert data["selected_warehouse"] is not None
    assert "risk_score" in data
    assert "fraud_status" in data
    assert len(data["decision_log"]) >= 5
    assert len(data["course_trace"]) == 3
    assert len(data["model_evaluations"]) == 2


def test_create_order_out_of_stock(client: TestClient) -> None:
    payload = {
        "user_id": "test-user",
        "items": [{"product_id": "p-9999", "quantity": 1}],
        "shipping_distance": 10,
        "is_new_user": False,
    }
    response = client.post("/orders", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["order_status"] == "rejected_out_of_stock"
    assert data["selected_warehouse"] is None


def test_create_order_high_risk(client: TestClient) -> None:
    payload = {
        "user_id": "new-user",
        "items": [{"product_id": "p-1002", "quantity": 5}],
        "shipping_distance": 50,
        "is_new_user": True,
    }
    response = client.post("/orders", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["fraud_status"] == "review_required"


def test_create_order_invalid_payload(client: TestClient) -> None:
    payload = {
        "user_id": "test-user",
        "items": [],
        "shipping_distance": 10,
        "is_new_user": False,
    }
    response = client.post("/orders", json=payload)
    assert response.status_code == 422


def test_list_agents(client: TestClient) -> None:
    response = client.get("/agents")
    assert response.status_code == 200
    data = response.json()
    assert "agents" in data
    assert "Order Agent" in data["agents"]
    assert "Fraud Detection Agent" in data["agents"]


def test_course_map(client: TestClient) -> None:
    response = client.get("/agents/course-map")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 3
    modules = [item["module"] for item in data]
    assert "COMP315 Cloud Computing" in modules
    assert "COMP310 Multi-Agent Systems" in modules
    assert "ELEC320 Neural Networks" in modules


def test_model_evaluations_endpoint(client: TestClient) -> None:
    response = client.get("/agents/model-evaluations")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 3
    model_names = [item["model_name"] for item in data]
    assert "Demand Prediction MLP Interface" in model_names
    assert "Fraud Detection Classifier Interface" in model_names
    assert "Product Category Classifier" in model_names


def test_cors_headers_present(client: TestClient) -> None:
    response = client.options(
        "/health",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert response.status_code == 200
    assert "access-control-allow-origin" in response.headers


def test_order_response_has_bids(client: TestClient) -> None:
    payload = {
        "user_id": "test-user",
        "items": [{"product_id": "p-1001", "quantity": 1}],
        "shipping_distance": 10,
        "is_new_user": False,
    }
    response = client.post("/orders", json=payload)
    data = response.json()
    assert len(data["bids"]) == 3
    for bid in data["bids"]:
        assert "warehouse_id" in bid
        assert "bid" in bid
        assert "suitability_score" in bid
        assert "reason" in bid


def test_order_restock_recommendation_present(client: TestClient) -> None:
    payload = {
        "user_id": "test-user",
        "items": [{"product_id": "p-1001", "quantity": 1}],
        "shipping_distance": 10,
        "is_new_user": False,
    }
    response = client.post("/orders", json=payload)
    data = response.json()
    assert data["restock_recommendation"] in {"restock recommended", "no restock needed"}


def test_multiple_products_order(client: TestClient) -> None:
    payload = {
        "user_id": "test-user",
        "items": [
            {"product_id": "p-1001", "quantity": 2},
            {"product_id": "p-1002", "quantity": 1},
        ],
        "shipping_distance": 15,
        "is_new_user": True,
    }
    response = client.post("/orders", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["order_total"] > 0
    assert len(data["bids"]) == 3
