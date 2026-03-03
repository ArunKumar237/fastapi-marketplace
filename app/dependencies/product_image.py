from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.repositories.store import StoreRepository
from app.services.product_image import ProductImageService


def get_product_image_service(
    db: AsyncSession = Depends(get_db),
) -> ProductImageService:
    return ProductImageService(
        db=db,
        store_repo=StoreRepository(db),
    )
