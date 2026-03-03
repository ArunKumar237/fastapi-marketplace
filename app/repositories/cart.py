import uuid

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.cart_item import CartItem
from app.models.product import Product


class CartRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_cart_items(self, user_id: uuid.UUID) -> list[CartItem]:
        result = await self.db.execute(
            select(CartItem)
            .options(joinedload(CartItem.product).joinedload(Product.images))
            .where(CartItem.user_id == user_id)
            .order_by(CartItem.created_at.asc())
        )
        return list(result.unique().scalars().all())

    async def get_cart_item(
        self,
        user_id: uuid.UUID,
        product_id: uuid.UUID,
    ) -> CartItem | None:
        result = await self.db.execute(
            select(CartItem)
            .options(joinedload(CartItem.product).joinedload(Product.images))
            .where(CartItem.user_id == user_id, CartItem.product_id == product_id)
        )
        return result.unique().scalar_one_or_none()

    async def create_cart_item(
        self,
        user_id: uuid.UUID,
        product_id: uuid.UUID,
        quantity: int,
    ) -> CartItem:
        cart_item = CartItem(user_id=user_id, product_id=product_id, quantity=quantity)
        self.db.add(cart_item)
        await self.db.commit()
        await self.db.refresh(cart_item)
        return cart_item

    async def update_cart_item_quantity(self, cart_item: CartItem, quantity: int) -> CartItem:
        cart_item.quantity = quantity
        await self.db.commit()
        await self.db.refresh(cart_item)
        return cart_item

    async def delete_cart_item(self, cart_item: CartItem) -> None:
        await self.db.delete(cart_item)
        await self.db.commit()

    async def clear_cart(self, user_id: uuid.UUID) -> None:
        await self.db.execute(delete(CartItem).where(CartItem.user_id == user_id))
        await self.db.commit()
