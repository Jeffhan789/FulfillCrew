from fastapi import APIRouter

from backend.database.db import product_service
from backend.database.models import Product

router = APIRouter(prefix="/products", tags=["products"])


@router.get("", response_model=list[Product])
def list_products() -> list[Product]:
    return product_service.list_products()

