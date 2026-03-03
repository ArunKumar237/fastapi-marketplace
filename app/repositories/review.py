import uuid
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.review import Review


class ReviewRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_review(
        self,
        user_id: uuid.UUID,
        product_id: uuid.UUID,
        rating: int,
        comment: str | None,
    ) -> Review:
        review = Review(
            user_id=user_id,
            product_id=product_id,
            rating=rating,
            comment=comment,
        )
        self.db.add(review)
        await self.db.commit()
        await self.db.refresh(review)
        return review

    async def get_product_reviews(
        self,
        product_id: uuid.UUID,
        skip: int,
        limit: int,
    ) -> tuple[list[Review], int]:
        total_result = await self.db.execute(
            select(func.count(Review.id)).where(Review.product_id == product_id)
        )
        total = total_result.scalar_one()

        result = await self.db.execute(
            select(Review)
            .options(joinedload(Review.user))
            .where(Review.product_id == product_id)
            .order_by(Review.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.unique().scalars().all()), total

    async def get_review_aggregates(self, product_id: uuid.UUID) -> tuple[float, int]:
        result = await self.db.execute(
            select(func.avg(Review.rating), func.count(Review.id)).where(
                Review.product_id == product_id
            )
        )
        avg_rating, review_count = result.one()
        average_rating = round(float(avg_rating), 1) if avg_rating is not None else 0.0
        return average_rating, int(review_count or 0)

    async def review_exists(self, user_id: uuid.UUID, product_id: uuid.UUID) -> bool:
        result = await self.db.execute(
            select(Review.id).where(
                Review.user_id == user_id,
                Review.product_id == product_id,
            )
        )
        return result.scalar_one_or_none() is not None

    async def user_purchased_product(self, user_id: uuid.UUID, product_id: uuid.UUID) -> bool:
        result = await self.db.execute(
            select(OrderItem.id)
            .join(Order, Order.id == OrderItem.order_id)
            .where(
                and_(
                    Order.user_id == user_id,
                    OrderItem.product_id == product_id,
                    func.upper(Order.status) == "DELIVERED",
                )
            )
            .limit(1)
        )
        return result.scalar_one_or_none() is not None
