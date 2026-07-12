"""Warehouse bid repository for PostgreSQL persistence."""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.models import WarehouseBidORM


class WarehouseBidRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def save(self, bid: WarehouseBidORM) -> None:
        self.session.add(bid)

    async def list_by_order(self, order_id: str) -> list[WarehouseBidORM]:
        result = await self.session.execute(
            select(WarehouseBidORM).where(WarehouseBidORM.order_id == order_id)
        )
        return list(result.scalars().all())
