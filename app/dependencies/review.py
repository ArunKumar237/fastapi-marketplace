from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.repositories.product import ProductRepository
from app.repositories.review import ReviewRepository
from app.services.review import ReviewService


def get_review_service(db: AsyncSession = Depends(get_db)) -> ReviewService:
    return ReviewService(
        review_repo=ReviewRepository(db),
        product_repo=ProductRepository(db),
    )
