from ml_models.product_category_classifier.model import classify_category


def predict_category(product: dict) -> str:
    return classify_category(str(product.get("name", "")))

