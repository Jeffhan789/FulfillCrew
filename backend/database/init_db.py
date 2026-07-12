"""Initialize the database with cleaned product data."""
import asyncio
import json
from pathlib import Path

from backend.database.engine import init_db, AsyncSessionLocal
from backend.database.models import ProductORM


async def seed_products():
    """Load cleaned products from JSON into the database."""
    repo_root = Path(__file__).resolve().parents[2]
    data_path = repo_root / "data_cleaning" / "cleaned_products" / "products.json"

    raw_products = json.loads(data_path.read_text(encoding="utf-8"))

    async with AsyncSessionLocal() as session:
        for item in raw_products:
            product = ProductORM(
                id=item["id"],
                name=item["name"],
                price=item["price"],
                category=item["category"],
                type=item["type"],
                quantity=item["quantity"],
                rating=item["rating"],
                image_link=item.get("image_link", ""),
            )
            session.add(product)
        await session.commit()
    print(f"Seeded {len(raw_products)} products into PostgreSQL.")


async def main():
    await init_db()
    await seed_products()


if __name__ == "__main__":
    asyncio.run(main())
