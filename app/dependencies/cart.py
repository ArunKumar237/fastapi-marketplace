from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.repositories.cart import CartRepository
from app.repositories.product import ProductRepository
from app.services.cart import CartService


def get_cart_service(db: AsyncSession = Depends(get_db)) -> CartService:
    return CartService(
        cart_repo=CartRepository(db),
        product_repo=ProductRepository(db),
    )
