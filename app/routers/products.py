import uuid
from decimal import Decimal

from fastapi import APIRouter, Depends, Query, Response, status

from app.dependencies.auth import get_current_user_optional
from app.dependencies.product import get_product_service
from app.dependencies.roles import require_vendor
from app.models.user import User
from app.schemas.pagination import PaginatedResponse
from app.schemas.product import (
    ProductCreate,
    ProductListResponse,
    ProductResponse,
    ProductUpdate,
)
from app.services.product import ProductService

router = APIRouter(prefix="/api/v1/products", tags=["Products"])


@router.post("", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
    product_data: ProductCreate,
    current_user: User = Depends(require_vendor),
    product_service: ProductService = Depends(get_product_service),
):
    return await product_service.create_product(current_user, product_data)


@router.get(
    "",
    response_model=PaginatedResponse[ProductListResponse],
    status_code=status.HTTP_200_OK,
)
async def list_products(
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
    category_id: uuid.UUID | None = None,
    store_id: uuid.UUID | None = None,
    min_price: Decimal | None = Query(default=None, gt=0),
    max_price: Decimal | None = Query(default=None, gt=0),
    search: str | None = Query(default=None),
    sort_by: str = Query(default="created_at"),
    sort_order: str = Query(default="desc"),
    current_user: User | None = Depends(get_current_user_optional),
    product_service: ProductService = Depends(get_product_service),
):
    include_inactive = False
    if current_user and store_id:
        vendor_store = await product_service.store_repo.get_by_owner_id(current_user.id)
        include_inactive = bool(vendor_store and vendor_store.id == store_id)

    return await product_service.list_products(
        page=page,
        size=size,
        category_id=category_id,
        store_id=store_id,
        min_price=min_price,
        max_price=max_price,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order,
        include_inactive=include_inactive,
    )


@router.get(
    "/{product_id}",
    response_model=ProductResponse,
    status_code=status.HTTP_200_OK,
)
async def get_product_detail(
    product_id: uuid.UUID,
    current_user: User | None = Depends(get_current_user_optional),
    product_service: ProductService = Depends(get_product_service),
):
    return await product_service.get_product(
        product_id=product_id,
        current_user=current_user,
    )


@router.put(
    "/{product_id}",
    response_model=ProductResponse,
    status_code=status.HTTP_200_OK,
)
async def update_product(
    product_id: uuid.UUID,
    updates: ProductUpdate,
    current_user: User = Depends(require_vendor),
    product_service: ProductService = Depends(get_product_service),
):
    return await product_service.update_product(product_id, current_user, updates)


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(
    product_id: uuid.UUID,
    current_user: User = Depends(require_vendor),
    product_service: ProductService = Depends(get_product_service),
):
    await product_service.delete_product(product_id, current_user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
