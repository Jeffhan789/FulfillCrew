"""Product API Router — catalogue listing endpoint.

This is a thin API layer that delegates to ProductService. It follows the
RESTful design pattern where GET /products returns the full catalogue.

Pagination Note:
    Currently returns all products. For production, add skip/limit query params
    and use SQL OFFSET/LIMIT for database-level pagination.

Caching Note:
    Product catalogues are read-heavy and change infrequently. In production
    you'd add HTTP Cache-Control headers and Redis caching.

Interview Note:
    Q: Why a separate /products endpoint instead of embedding in /orders?
    A: RESTful resource separation. Products are an independent domain entity
       with their own lifecycle. A separate endpoint enables product browsing
       without creating an order, and allows different caching strategies.
"""

from fastapi import APIRouter

from backend.schemas import Product
from backend.services.product_service import ProductService

router = APIRouter(prefix="/products", tags=["products"])


@router.get("", response_model=list[Product])
async def list_products() -> list[Product]:
    service = ProductService()
    return await service.list_products()
