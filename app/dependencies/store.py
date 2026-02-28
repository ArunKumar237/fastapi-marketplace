from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.repositories.store import StoreRepository
from app.services.store import StoreService


def get_store_service(db: AsyncSession = Depends(get_db)) -> StoreService:
    return StoreService(StoreRepository(db))
