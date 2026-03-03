from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.repositories.address import AddressRepository
from app.services.address import AddressService


def get_address_service(db: AsyncSession = Depends(get_db)) -> AddressService:
    return AddressService(address_repo=AddressRepository(db))
