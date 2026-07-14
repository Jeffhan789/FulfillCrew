"""Product Service — application service layer for product catalogue access.

Implements the Circuit Breaker pattern implicitly: if the database is
unreachable, it falls back to the JSON file from the data_cleaning pipeline.
This ensures the system remains functional even during partial outages.

Architecture Layers:
    API (products.py) → Service (ProductService) → Repository (ProductRepository) → DB (PostgreSQL)
                                    ↓
                               Fallback (JSON file)

Data Flow:
    1. data_cleaning/ scripts clean raw product data → products.json
    2. ProductService loads JSON as fallback catalogue
    3. FastAPI startup (init_db) seeds PostgreSQL from JSON if tables are empty
    4. Runtime reads prefer PostgreSQL, fall back to JSON on DB errors

Engineering Note:
    Q: Why JSON fallback instead of just failing when the DB is down?
    A: Graceful degradation. In a demo/school project, having a working
       frontend is more important than perfect persistence. The JSON
       fallback lets the system serve products even if PostgreSQL is not
       running.
       
    Q: How would you improve this for production?
    A: 1. Redis cache with TTL for hot products
       2. Database connection pooling with circuit breaker (e.g., pybreaker)
       3. Event-driven cache invalidation when stock changes
       4. Full-text search (PostgreSQL tsvector or Elasticsearch) for product discovery
"""
import json
from pathlib import Path

from backend.database.engine import AsyncSessionLocal
from backend.database.models import ProductORM
from backend.repositories.product_repository import ProductRepository
from backend.schemas import Product


class ProductService:
    def __init__(self, products: dict[str, Product] | None = None) -> None:
        self._fallback_products = products or self._load_products_from_json()

    @property
    def products(self) -> dict[str, Product]:
        """Expose the in-memory catalogue used by the graceful fallback path."""
        return self._fallback_products

    @products.setter
    def products(self, products: dict[str, Product]) -> None:
        self._fallback_products = products

    def _load_products_from_json(self) -> dict[str, Product]:
        repo_root = Path(__file__).resolve().parents[2]
        data_path = repo_root / "data_cleaning" / "cleaned_products" / "products.json"
        raw_products = json.loads(data_path.read_text(encoding="utf-8"))
        return {item["id"]: Product(**item) for item in raw_products}

    def _orm_to_product(self, orm: ProductORM) -> Product:
        return Product(
            id=orm.id,
            name=orm.name,
            price=orm.price,
            category=orm.category,
            type=orm.type,
            quantity=orm.quantity,
            rating=orm.rating,
            image_link=orm.image_link or "",
        )

    async def list_products(self) -> list[Product]:
        try:
            async with AsyncSessionLocal() as session:
                repo = ProductRepository(session)
                orms = await repo.list_all()
                return [self._orm_to_product(p) for p in orms]
        except Exception:
            return list(self._fallback_products.values())

    async def get_product_map(self) -> dict[str, Product]:
        try:
            async with AsyncSessionLocal() as session:
                repo = ProductRepository(session)
                orms = await repo.list_all()
                return {p.id: self._orm_to_product(p) for p in orms}
        except Exception:
            return self._fallback_products
