from fastapi import APIRouter
from backend.schemas import Product
from backend.services.product_service import ProductService

router = APIRouter(prefix="/products", tags=["products"])


@router.get("", response_model=list[Product])
async def list_products() -> list[Product]:
    service = ProductService()
    return await service.list_products()
