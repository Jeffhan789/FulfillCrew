"""Product repository for PostgreSQL persistence."""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.models import ProductORM


class ProductRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, product_id: str) -> ProductORM | None:
        result = await self.session.execute(
            select(ProductORM).where(ProductORM.id == product_id)
        )
        return result.scalar_one_or_none()

    async def list_all(self) -> list[ProductORM]:
        result = await self.session.execute(select(ProductORM))
        return list(result.scalars().all())

    async def update_stock(self, product_id: str, delta: int) -> None:
        product = await self.get_by_id(product_id)
        if product is not None:
            product.quantity += delta

    async def save(self, product: ProductORM) -> None:
        self.session.add(product)
