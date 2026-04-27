import json
from pathlib import Path

from backend.database.models import Product


class ProductService:
    def __init__(self) -> None:
        self.products = self._load_products()

    def _load_products(self) -> dict[str, Product]:
        repo_root = Path(__file__).resolve().parents[2]
        data_path = repo_root / "data_cleaning" / "cleaned_products" / "products.json"
        raw_products = json.loads(data_path.read_text(encoding="utf-8"))
        return {item["id"]: Product(**item) for item in raw_products}

    def list_products(self) -> list[Product]:
        return list(self.products.values())

    def get_product_map(self) -> dict[str, Product]:
        return self.products

