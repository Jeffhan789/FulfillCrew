"""Order repository for PostgreSQL persistence."""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.database.models import AgentDecisionORM, OrderItemORM, OrderORM, WarehouseBidORM


class OrderRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_order(self, order: OrderORM) -> OrderORM:
        self.session.add(order)
        await self.session.flush()
        return order

    async def get_by_id(self, order_id: str) -> OrderORM | None:
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
        for item in items:
            item.order_id = order_id
            self.session.add(item)

    async def add_decisions(self, order_id: str, decisions: list[AgentDecisionORM]) -> None:
        for decision in decisions:
            decision.order_id = order_id
            self.session.add(decision)

    async def add_bids(self, order_id: str, bids: list[WarehouseBidORM]) -> None:
        for bid in bids:
            bid.order_id = order_id
            self.session.add(bid)

    async def update_order_status(self, order_id: str, status: str, selected_warehouse: str | None) -> None:
        order = await self.get_by_id(order_id)
        if order is not None:
            order.order_status = status
            order.selected_warehouse = selected_warehouse
