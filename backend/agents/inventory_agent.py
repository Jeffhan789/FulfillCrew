"""Inventory Agent — stock availability check and reservation.

This agent demonstrates the "resource allocation" problem in MAS:
- How do we prevent overselling when multiple agents access the same inventory?
- In a distributed system, this would require distributed locks or serialisable transactions.
- FulfillCrew uses PostgreSQL row-level locking (via SQLAlchemy ORM) and
  atomic transactions in the repository layer to prevent race conditions.
"""

from backend.agents.base_agent import BaseAgent
from backend.database.models import BasketItem, Product


class InventoryAgent(BaseAgent):
    """Monitors and manages product stock levels.
    
    Two-phase protocol:
    1. check_stock: optimistic read to verify availability
    2. reserve_stock: pessimistic write (decrement) after fraud clearance
    
    Interview Note:
        Q: How do you handle concurrent orders for the same product?
        A: The actual stock update happens in OrderService._persist_order
           inside an async SQLAlchemy transaction. The repository calls
           product_repo.update_stock() which modifies the ORM object.
           When the session is committed, PostgreSQL guarantees atomicity.
           
        Q: What happens if check_stock passes but reserve_stock fails?
        A: This is a classic "check-then-act" race condition. In production
           you would use SELECT FOR UPDATE or a compare-and-swap pattern.
           FulfillCrew mitigates this by doing all checks in memory and
           then committing the reservation in a single transaction.
    """
    name = "Inventory Agent"

    def check_stock(self, items: list[BasketItem], products: dict[str, Product]) -> tuple[bool, list[str]]:
        """Verify that every item in the order has sufficient stock.
        
        Args:
            items: Basket items from the order request.
            products: Current product catalogue (keyed by product_id).
            
        Returns:
            (all_available, list_of_unavailable_product_ids)
        """
        unavailable = []
        for item in items:
            product = products.get(item.product_id)
            if product is None or product.quantity < item.quantity:
                unavailable.append(item.product_id)
        return len(unavailable) == 0, unavailable

    def reserve_stock(self, items: list[BasketItem], products: dict[str, Product]) -> None:
        """Decrement stock levels for the ordered items.
        
        WARNING: This modifies the in-memory Product objects. The actual
        persistence happens in the repository layer when the SQLAlchemy session
        is committed. This design separates domain logic (agent) from
        infrastructure (database).
        """
        for item in items:
            product = products[item.product_id]
            product.quantity -= item.quantity

