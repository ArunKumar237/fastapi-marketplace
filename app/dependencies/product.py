from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.repositories.category import CategoryRepository
from app.repositories.product import ProductRepository
from app.repositories.store import StoreRepository
from app.services.product import ProductService


def get_product_service(db: AsyncSession = Depends(get_db)) -> ProductService:
    return ProductService(
        product_repo=ProductRepository(db),
        store_repo=StoreRepository(db),
        category_repo=CategoryRepository(db),
    )
