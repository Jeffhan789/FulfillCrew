import json
from pathlib import Path

from backend.database.engine import AsyncSessionLocal
from backend.database.models import ProductORM
from backend.repositories.product_repository import ProductRepository
from backend.schemas import Product


class ProductService:
    def __init__(self) -> None:
        self._fallback_products = self._load_products_from_json()

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
