import uuid

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError

from app.models.user import User
from app.repositories.product import ProductRepository
from app.repositories.review import ReviewRepository
from app.schemas.review import ReviewCreate, ReviewListResponse, ReviewResponse


class ReviewService:
    def __init__(self, review_repo: ReviewRepository, product_repo: ProductRepository):
        self.review_repo = review_repo
        self.product_repo = product_repo

    async def create_review(
        self,
        user: User,
        product_id: uuid.UUID,
        payload: ReviewCreate,
    ) -> ReviewResponse:
        product = await self.product_repo.get_by_id(product_id, include_inactive=True)
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found",
            )

        purchased = await self.review_repo.user_purchased_product(user.id, product_id)
        if not purchased:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only review products you purchased",
            )

        already_reviewed = await self.review_repo.review_exists(user.id, product_id)
        if already_reviewed:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="You have already reviewed this product",
            )

        try:
            review = await self.review_repo.create_review(
                user_id=user.id,
                product_id=product_id,
                rating=payload.rating,
                comment=payload.comment,
            )
        except IntegrityError:
            await self.review_repo.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="You have already reviewed this product",
            )

        return ReviewResponse(
            id=review.id,
            user_id=review.user_id,
            product_id=review.product_id,
            reviewer_name=user.full_name,
            rating=review.rating,
            comment=review.comment,
            created_at=review.created_at,
        )

    async def get_product_reviews(
        self,
        product_id: uuid.UUID,
        page: int,
        size: int,
    ) -> ReviewListResponse:
        product = await self.product_repo.get_by_id(product_id, include_inactive=True)
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found",
            )

        skip = (page - 1) * size
        reviews, total = await self.review_repo.get_product_reviews(
            product_id=product_id,
            skip=skip,
            limit=size,
        )
        average_rating, review_count = await self.review_repo.get_review_aggregates(
            product_id
        )

        items = [
            ReviewResponse(
                id=review.id,
                user_id=review.user_id,
                product_id=review.product_id,
                reviewer_name=review.user.full_name,
                rating=review.rating,
                comment=review.comment,
                created_at=review.created_at,
            )
            for review in reviews
        ]

        return ReviewListResponse(
            items=items,
            page=page,
            size=size,
            total=total,
            average_rating=average_rating,
            review_count=review_count,
        )
