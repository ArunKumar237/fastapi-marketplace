from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.repositories.cart import CartRepository
from app.repositories.order import OrderItemRepository, OrderRepository
from app.repositories.store import StoreRepository
from app.services.order import OrderService


def get_order_service(db: AsyncSession = Depends(get_db)) -> OrderService:
    return OrderService(
        order_repo=OrderRepository(db),
        order_item_repo=OrderItemRepository(db),
        cart_repo=CartRepository(db),
        store_repo=StoreRepository(db),
    )
