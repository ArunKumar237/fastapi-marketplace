import uuid

from sqlalchemy import desc, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.address import Address
from app.models.order import Order


class AddressRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_address(self, user_id: uuid.UUID, data: dict) -> Address:
        address = Address(user_id=user_id, **data)
        self.db.add(address)
        await self.db.commit()
        await self.db.refresh(address)
        return address

    async def get_user_addresses(self, user_id: uuid.UUID) -> list[Address]:
        result = await self.db.execute(
            select(Address)
            .where(Address.user_id == user_id)
            .order_by(desc(Address.is_default), desc(Address.created_at))
        )
        return list(result.scalars().all())

    async def get_user_address_by_id(
        self, user_id: uuid.UUID, address_id: uuid.UUID
    ) -> Address | None:
        result = await self.db.execute(
            select(Address).where(
                Address.id == address_id,
                Address.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    async def unset_default_addresses(self, user_id: uuid.UUID) -> None:
        await self.db.execute(
            update(Address)
            .where(Address.user_id == user_id, Address.is_default.is_(True))
            .values(is_default=False)
        )
        await self.db.commit()

    async def update_address(self, address: Address, data: dict) -> Address:
        for field, value in data.items():
            setattr(address, field, value)
        await self.db.commit()
        await self.db.refresh(address)
        return address

    async def delete_address(self, address: Address) -> None:
        await self.db.delete(address)
        await self.db.commit()

    async def get_most_recent_address(self, user_id: uuid.UUID) -> Address | None:
        result = await self.db.execute(
            select(Address)
            .where(Address.user_id == user_id)
            .order_by(desc(Address.created_at))
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def is_address_used_in_orders(
        self, user_id: uuid.UUID, address_id: uuid.UUID
    ) -> bool:
        result = await self.db.execute(
            select(Order.id).where(
                Order.user_id == user_id,
                Order.shipping_address_id == address_id,
            )
        )
        return result.scalar_one_or_none() is not None
