import uuid

from fastapi import APIRouter, Depends, Query, status

from app.dependencies.auth import get_current_user
from app.dependencies.review import get_review_service
from app.models.user import User
from app.schemas.review import ReviewCreate, ReviewListResponse, ReviewResponse
from app.services.review import ReviewService

router = APIRouter(prefix="/api/v1/products/{product_id}/reviews", tags=["Reviews"])


@router.post("", response_model=ReviewResponse, status_code=status.HTTP_201_CREATED)
async def create_review(
    product_id: uuid.UUID,
    payload: ReviewCreate,
    current_user: User = Depends(get_current_user),
    review_service: ReviewService = Depends(get_review_service),
):
    return await review_service.create_review(
        user=current_user,
        product_id=product_id,
        payload=payload,
    )


@router.get("", response_model=ReviewListResponse, status_code=status.HTTP_200_OK)
async def list_product_reviews(
    product_id: uuid.UUID,
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
    review_service: ReviewService = Depends(get_review_service),
):
    return await review_service.get_product_reviews(
        product_id=product_id,
        page=page,
        size=size,
    )
