import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


class UserRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    # -------------------------
    # Get user by ID
    # -------------------------
    async def get_by_id(self, user_id: uuid.UUID) -> User | None:
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    # -------------------------
    # Get user by Email
    # -------------------------
    async def get_by_email(self, email: str) -> User | None:
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    # -------------------------
    # Create new user
    # -------------------------
    async def create(self, user_data: dict) -> User:
        user = User(**user_data)

        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)

        return user

    async def update(self, user: User, data: dict) -> User:
        """
        Apply a dict of changes to a User instance, commit, and return
        the refreshed object.
        """
        for field, value in data.items():
            setattr(user, field, value)
        await self.db.commit()
        await self.db.refresh(user)
        return user
