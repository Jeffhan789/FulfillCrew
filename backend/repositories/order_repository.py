"""Order repository for PostgreSQL persistence.

Implements the Repository Pattern — abstracts all database operations
behind a clean interface. This decouples the business logic (OrderService)
from the data access layer (SQLAlchemy), making unit testing trivial.

Why Repository Pattern?
    - Testability: Mock the repository instead of spinning up a real DB
    - Flexibility: Swap PostgreSQL for MongoDB without touching services
    - Clarity: Each repository has a single responsibility (CRUD for one entity)

Interview Note:
    Q: What's the difference between Repository and Active Record?
    A: Repository separates data access from the domain model. Active Record
       (e.g., Django ORM) combines them. Repository is better for complex
       business logic because the domain model stays pure.
       
    Q: Why use selectinload() in get_by_id()?
    A: selectinload() is a joined eager loading strategy. It fetches related
       objects (items, decisions, bids) in a second SELECT using IN clause.
       This avoids N+1 query problems while still being efficient for
       one-to-many relationships.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.database.models import AgentDecisionORM, OrderItemORM, OrderORM, WarehouseBidORM


class OrderRepository:
    """CRUD operations for OrderORM and related entities."""
    
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_order(self, order: OrderORM) -> OrderORM:
        """Insert a new order into the database."""
        self.session.add(order)
        await self.session.flush()
        return order

    async def get_by_id(self, order_id: str) -> OrderORM | None:
        """Fetch an order by ID with all related entities eagerly loaded.
        
        Uses selectinload to fetch items, decisions, and bids in a single
        additional query, avoiding the N+1 problem.
        """
        result = await self.session.execute(
            select(OrderORM)
            .where(OrderORM.order_id == order_id)
            .options(
                selectinload(OrderORM.items),
                selectinload(OrderORM.decisions),
                selectinload(OrderORM.bids),
            )
        )
        return result.scalar_one_or_none()

    async def add_items(self, order_id: str, items: list[OrderItemORM]) -> None:
        """Associate line items with an order."""
        for item in items:
            item.order_id = order_id
            self.session.add(item)

    async def add_decisions(self, order_id: str, decisions: list[AgentDecisionORM]) -> None:
        """Associate agent decisions with an order."""
        for decision in decisions:
            decision.order_id = order_id
            self.session.add(decision)

    async def add_bids(self, order_id: str, bids: list[WarehouseBidORM]) -> None:
        """Associate warehouse bids with an order."""
        for bid in bids:
            bid.order_id = order_id
            self.session.add(bid)

    async def update_order_status(self, order_id: str, status: str, selected_warehouse: str | None) -> None:
        """Update the status and selected warehouse for an order."""
        order = await self.get_by_id(order_id)
        if order is not None:
            order.order_status = status
            order.selected_warehouse = selected_warehouse
