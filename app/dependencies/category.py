from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.repositories.category import CategoryRepository
from app.services.category import CategoryService


def get_category_service(db: AsyncSession = Depends(get_db)) -> CategoryService:
    return CategoryService(CategoryRepository(db))
