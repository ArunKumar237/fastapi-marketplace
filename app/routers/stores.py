import uuid

from fastapi import APIRouter, Depends, Query, status

from app.dependencies.auth import get_current_user_optional
from app.dependencies.roles import require_admin, require_vendor
from app.dependencies.store import get_store_service
from app.models.user import User, UserRole
from app.schemas.store import (
    StoreCreate,
    StoreListResponse,
    StoreResponse,
    StoreStatusUpdate,
    StoreUpdate,
)
from app.services.store import StoreService

router = APIRouter(prefix="/api/v1/stores", tags=["Stores"])


@router.post("", response_model=StoreResponse, status_code=status.HTTP_201_CREATED)
async def create_store(
    store_data: StoreCreate,
    current_user: User = Depends(require_vendor),
    store_service: StoreService = Depends(get_store_service),
):
    return await store_service.create_store(
        current_user=current_user, store_data=store_data
    )


@router.get("", response_model=StoreListResponse, status_code=status.HTTP_200_OK)
async def list_stores(
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
    current_user: User | None = Depends(get_current_user_optional),
    store_service: StoreService = Depends(get_store_service),
):
    include_inactive = bool(current_user and current_user.role == UserRole.ADMIN)
    items, total = await store_service.list_stores(
        page=page,
        size=size,
        include_inactive=include_inactive,
    )
    return StoreListResponse(page=page, size=size, total=total, items=items)


@router.get("/{store_id}", response_model=StoreResponse, status_code=status.HTTP_200_OK)
async def get_store_by_id(
    store_id: uuid.UUID,
    store_service: StoreService = Depends(get_store_service),
):
    return await store_service.get_store_public_profile(store_id)


@router.put("/{store_id}", response_model=StoreResponse, status_code=status.HTTP_200_OK)
async def update_store(
    store_id: uuid.UUID,
    updates: StoreUpdate,
    current_user: User = Depends(require_vendor),
    store_service: StoreService = Depends(get_store_service),
):
    return await store_service.update_store(
        store_id=store_id,
        current_user=current_user,
        updates=updates,
    )


@router.patch(
    "/{store_id}/status", response_model=StoreResponse, status_code=status.HTTP_200_OK
)
async def update_store_status(
    store_id: uuid.UUID,
    status_data: StoreStatusUpdate,
    _: User = Depends(require_admin),
    store_service: StoreService = Depends(get_store_service),
):
    return await store_service.update_store_status(
        store_id=store_id,
        is_active=status_data.is_active,
    )
