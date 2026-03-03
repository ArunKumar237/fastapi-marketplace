import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.order import Order
from app.models.order_item import OrderItem


class OrderRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_order(
        self,
        user_id: uuid.UUID,
        shipping_address_id: uuid.UUID,
        total_amount,
        order_number: str,
    ) -> Order:
        order = Order(
            user_id=user_id,
            shipping_address_id=shipping_address_id,
            status="pending",
            total_amount=total_amount,
            order_number=order_number,
        )
        self.db.add(order)
        await self.db.flush()
        await self.db.refresh(order)
        return order

    async def get_user_orders(
        self,
        user_id: uuid.UUID,
        page: int,
        size: int,
        status: str | None = None,
    ) -> tuple[list[Order], int]:
        filters = [Order.user_id == user_id]
        if status:
            filters.append(Order.status == status)

        total_result = await self.db.execute(
            select(func.count(Order.id)).where(*filters)
        )
        total = total_result.scalar_one()

        result = await self.db.execute(
            select(Order)
            .where(*filters)
            .order_by(Order.created_at.desc())
            .offset((page - 1) * size)
            .limit(size)
        )
        return list(result.scalars().all()), total

    async def get_order_by_id(self, order_id: uuid.UUID) -> Order | None:
        result = await self.db.execute(
            select(Order)
            .options(
                joinedload(Order.address),
                joinedload(Order.order_items).joinedload(OrderItem.product),
            )
            .where(Order.id == order_id)
        )
        return result.unique().scalar_one_or_none()

    async def get_order_by_number(self, order_number: str) -> Order | None:
        result = await self.db.execute(
            select(Order).where(Order.order_number == order_number)
        )
        return result.scalar_one_or_none()

    async def update_order_status(self, order: Order, status: str) -> Order:
        order.status = status
        await self.db.flush()
        return order


class OrderItemRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_order_items(self, items: list[dict]) -> list[OrderItem]:
        order_items = [OrderItem(**item) for item in items]
        self.db.add_all(order_items)
        await self.db.flush()
        return order_items

    async def get_vendor_order_items(
        self,
        store_id: uuid.UUID,
        page: int,
        size: int,
    ) -> tuple[list[OrderItem], int]:
        total_result = await self.db.execute(
            select(func.count(OrderItem.id)).where(OrderItem.store_id == store_id)
        )
        total = total_result.scalar_one()

        result = await self.db.execute(
            select(OrderItem)
            .options(
                joinedload(OrderItem.order).joinedload(Order.user),
                joinedload(OrderItem.product),
            )
            .where(OrderItem.store_id == store_id)
            .order_by(OrderItem.created_at.desc())
            .offset((page - 1) * size)
            .limit(size)
        )
        return list(result.unique().scalars().all()), total

    async def get_order_item_by_id(self, order_item_id: uuid.UUID) -> OrderItem | None:
        result = await self.db.execute(
            select(OrderItem)
            .options(
                joinedload(OrderItem.order).joinedload(Order.user),
                joinedload(OrderItem.product),
            )
            .where(OrderItem.id == order_item_id)
        )
        return result.unique().scalar_one_or_none()

    async def get_order_items_by_order_id(self, order_id: uuid.UUID) -> list[OrderItem]:
        result = await self.db.execute(
            select(OrderItem).where(OrderItem.order_id == order_id)
        )
        return list(result.scalars().all())

    async def update_item_status(self, order_item: OrderItem, status: str) -> OrderItem:
        order_item.status = status
        await self.db.flush()
        return order_item
