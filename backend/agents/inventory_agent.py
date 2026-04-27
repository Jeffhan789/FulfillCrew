from backend.agents.base_agent import BaseAgent
from backend.database.models import BasketItem, Product


class InventoryAgent(BaseAgent):
    name = "Inventory Agent"

    def check_stock(self, items: list[BasketItem], products: dict[str, Product]) -> tuple[bool, list[str]]:
        unavailable = []
        for item in items:
            product = products.get(item.product_id)
            if product is None or product.quantity < item.quantity:
                unavailable.append(item.product_id)
        return len(unavailable) == 0, unavailable

    def reserve_stock(self, items: list[BasketItem], products: dict[str, Product]) -> None:
        for item in items:
            product = products[item.product_id]
            product.quantity -= item.quantity

