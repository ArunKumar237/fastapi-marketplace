import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.store import Store


class StoreRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, store_data: dict) -> Store:
        store = Store(**store_data)
        self.db.add(store)
        await self.db.commit()
        await self.db.refresh(store)
        return store

    async def get_by_id(self, store_id: uuid.UUID) -> Store | None:
        result = await self.db.execute(
            select(Store).options(selectinload(Store.owner)).where(Store.id == store_id)
        )
        return result.scalar_one_or_none()

    async def get_by_name(self, name: str) -> Store | None:
        result = await self.db.execute(select(Store).where(Store.name == name))
        return result.scalar_one_or_none()

    async def get_by_owner_id(self, owner_id: uuid.UUID) -> Store | None:
        result = await self.db.execute(select(Store).where(Store.owner_id == owner_id))
        return result.scalar_one_or_none()

    async def list(
        self,
        page: int = 1,
        size: int = 20,
        active_only: bool = True,
    ) -> tuple[list[Store], int]:
        filters = [Store.is_active.is_(True)] if active_only else []

        total_query = select(func.count(Store.id))
        if filters:
            total_query = total_query.where(*filters)
        total_result = await self.db.execute(total_query)
        total = total_result.scalar_one()

        query = (
            select(Store)
            .options(selectinload(Store.owner))
            .order_by(Store.created_at.desc())
            .offset((page - 1) * size)
            .limit(size)
        )
        if filters:
            query = query.where(*filters)

        result = await self.db.execute(query)
        stores = list(result.scalars().all())
        return stores, total

    async def update(self, store: Store, data: dict) -> Store:
        for field, value in data.items():
            setattr(store, field, value)
        await self.db.commit()
        await self.db.refresh(store)
        return store

    async def delete(self, store: Store) -> None:
        await self.db.delete(store)
        await self.db.commit()
