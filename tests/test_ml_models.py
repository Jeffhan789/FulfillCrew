from ml_models.demand_prediction.model import LightweightDemandMLP
from ml_models.demand_prediction.predict import predict_demand
from ml_models.fraud_detection.model import LightweightFraudClassifier
from ml_models.fraud_detection.predict import predict_risk
from ml_models.product_category_classifier.model import classify_category, KEYWORDS
from ml_models.product_category_classifier.predict import predict_category


# Demand Prediction Tests

def test_demand_mlp_returns_positive_integer() -> None:
    model = LightweightDemandMLP()
    result = model.predict([50.0, 10, 4.0, 1.0, 0.5])
    assert isinstance(result, int)
    assert result >= 1


def test_demand_prediction_higher_price_different_result() -> None:
    model = LightweightDemandMLP()
    low = model.predict([0.0, 0, 0.0, 0.0, 0.0])
    high = model.predict([500.0, 200, 5.0, 1.0, 1.0])
    assert low != high
    assert low < high


def test_demand_predict_with_electronics() -> None:
    product = {"price": 59.99, "quantity": 20, "rating": 4.5, "category": "electronics", "type": "audio"}
    result = predict_demand(product)
    assert isinstance(result, int)
    assert result >= 1


def test_demand_predict_with_non_electronics() -> None:
    product = {"price": 29.99, "quantity": 15, "rating": 3.5, "category": "fashion", "type": "wearable"}
    result = predict_demand(product)
    assert isinstance(result, int)
    assert result >= 1


def test_demand_predict_with_device_type() -> None:
    product = {"price": 199.99, "quantity": 5, "rating": 4.2, "category": "electronics", "type": "device"}
    result = predict_demand(product)
    assert isinstance(result, int)
    assert result >= 1


def test_demand_predict_with_empty_product() -> None:
    result = predict_demand({})
    assert isinstance(result, int)
    assert result >= 1


# Fraud Detection Tests

def test_fraud_classifier_returns_valid_probability() -> None:
    model = LightweightFraudClassifier()
    features = {
        "order_total": 50.0,
        "number_of_items": 2,
        "average_item_price": 25.0,
        "is_new_user": True,
        "shipping_distance": 10.0,
    }
    result = model.predict_proba(features)
    assert 0.0 <= result <= 1.0


def test_fraud_classifier_new_user_higher_risk() -> None:
    model = LightweightFraudClassifier()
    base = {"order_total": 50.0, "number_of_items": 2, "average_item_price": 25.0, "shipping_distance": 10.0}
    new_user = model.predict_proba({**base, "is_new_user": True})
    existing_user = model.predict_proba({**base, "is_new_user": False})
    assert new_user > existing_user


def test_fraud_classifier_high_distance_increases_risk() -> None:
    model = LightweightFraudClassifier()
    base = {"order_total": 50.0, "number_of_items": 2, "average_item_price": 25.0, "is_new_user": False}
    short = model.predict_proba({**base, "shipping_distance": 5.0})
    long = model.predict_proba({**base, "shipping_distance": 50.0})
    assert long > short


def test_predict_risk_interface() -> None:
    features = {
        "order_total": 100.0,
        "number_of_items": 3,
        "average_item_price": 33.33,
        "is_new_user": False,
        "shipping_distance": 15.0,
    }
    result = predict_risk(features)
    assert 0.0 <= result <= 1.0


def test_fraud_classifier_extreme_order() -> None:
    model = LightweightFraudClassifier()
    features = {
        "order_total": 10000.0,
        "number_of_items": 50,
        "average_item_price": 200.0,
        "is_new_user": True,
        "shipping_distance": 100.0,
    }
    result = model.predict_proba(features)
    assert 0.0 <= result <= 1.0
    assert result > 0.5


# Product Category Classification Tests

def test_classify_electronics_keywords() -> None:
    assert classify_category("Wireless Smart Watch") == "electronics"
    assert classify_category("Headphone Audio Device") == "electronics"


def test_classify_home_keywords() -> None:
    assert classify_category("Desk Lamp Light") == "home"
    assert classify_category("Kitchen Chair") == "home"


def test_classify_fashion_keywords() -> None:
    assert classify_category("Running Shoe") == "fashion"
    assert classify_category("Leather Jacket") == "fashion"


def test_classify_sports_keywords() -> None:
    assert classify_category("Fitness Ball Equipment") == "sports"


def test_classify_beauty_keywords() -> None:
    assert classify_category("Skin Care Cream") == "beauty"


def test_classify_books_keywords() -> None:
    assert classify_category("Novel Paperback Book") == "books"


def test_classify_unknown_defaults_to_electronics() -> None:
    assert classify_category("XYZ ABC Unknown") == "electronics"


def test_predict_category_interface() -> None:
    product = {"name": "Smart Watch", "price": 199.99}
    result = predict_category(product)
    assert result in KEYWORDS


def test_all_keywords_have_non_empty_sets() -> None:
    for category, words in KEYWORDS.items():
        assert len(words) > 0


def test_classify_case_insensitive() -> None:
    assert classify_category("WIRELESS SMART WATCH") == "electronics"
    assert classify_category("desk lamp") == "home"
