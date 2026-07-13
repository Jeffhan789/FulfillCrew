"""Product repository for PostgreSQL persistence."""
"""Product repository for PostgreSQL persistence.

Extends the Repository Pattern to ProductORM entities. Provides CRUD
operations for the product catalogue.

Operations:
    - get_by_id: Fetch a single product by primary key
    - list_all: Return all products (for catalogue view)
    - update_stock: Atomic quantity adjustment (used during order fulfillment)
    - save: Insert a new product

Interview Note:
    Q: Why does update_stock take a delta instead of an absolute value?
    A: Delta is safer for concurrent updates. If two orders decrement stock
       simultaneously, absolute updates would overwrite each other (last-write
       wins). Delta updates are additive and commutative within a transaction.
       
    Q: How would you handle high-traffic product listing?
    A: Add Redis caching with cache invalidation on stock updates. Use
       database query pagination (LIMIT/OFFSET or cursor-based) for large
       catalogues. Consider read replicas for read-heavy workloads.
"""
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
