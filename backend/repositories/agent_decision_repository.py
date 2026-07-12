"""Agent decision repository for PostgreSQL persistence."""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.models import AgentDecisionORM


class AgentDecisionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def save(self, decision: AgentDecisionORM) -> None:
        self.session.add(decision)

    async def list_by_order(self, order_id: str) -> list[AgentDecisionORM]:
        result = await self.session.execute(
            select(AgentDecisionORM).where(AgentDecisionORM.order_id == order_id)
        )
        return list(result.scalars().all())
