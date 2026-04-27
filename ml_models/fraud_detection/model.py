import math


class LightweightFraudClassifier:
    def predict_proba(self, features: dict) -> float:
        order_total = float(features.get("order_total", 0))
        number_of_items = float(features.get("number_of_items", 0))
        average_item_price = float(features.get("average_item_price", 0))
        is_new_user = 1.0 if features.get("is_new_user") else 0.0
        shipping_distance = float(features.get("shipping_distance", 0))

        logit = (
            -3.4
            + 0.004 * order_total
            + 0.08 * number_of_items
            + 0.003 * average_item_price
            + 0.75 * is_new_user
            + 0.006 * shipping_distance
        )
        return round(1 / (1 + math.exp(-logit)), 3)

