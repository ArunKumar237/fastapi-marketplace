import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks, Depends, Query, status

from app.dependencies.auth import get_current_user
from app.dependencies.orders import get_order_service
from app.dependencies.roles import require_vendor
from app.models.user import User
from app.schemas.order import (
    OrderCreate,
    OrderDetailResponse,
    OrderResponse,
    OrderStatusUpdate,
    VendorOrderItemResponse,
)
from app.schemas.pagination import PaginatedResponse
from app.services.order import OrderService, log_order_placement_event

router = APIRouter(prefix="/api/v1", tags=["Orders"])


@router.post(
    "/orders", response_model=OrderDetailResponse, status_code=status.HTTP_201_CREATED
)
async def place_order(
    payload: OrderCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    order_service: OrderService = Depends(get_order_service),
):
    order_response = await order_service.place_order(
        user=current_user,
        shipping_address_id=payload.shipping_address_id,
    )
    background_tasks.add_task(
        log_order_placement_event,
        order_id=str(order_response.id),
        user_email=current_user.email,
        timestamp=datetime.now(timezone.utc).isoformat(),
        order_details=order_response.model_dump(mode="json"),
    )
    return order_response


@router.get(
    "/me/orders",
    response_model=PaginatedResponse[OrderResponse],
    status_code=status.HTTP_200_OK,
)
async def list_my_orders(
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
    status: str | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    order_service: OrderService = Depends(get_order_service),
):
    return await order_service.get_user_orders(
        user=current_user,
        page=page,
        size=size,
        status=status,
    )


@router.get(
    "/me/orders/{order_id}",
    response_model=OrderDetailResponse,
    status_code=status.HTTP_200_OK,
)
async def get_my_order_detail(
    order_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    order_service: OrderService = Depends(get_order_service),
):
    return await order_service.get_user_order_detail(
        user=current_user,
        order_id=order_id,
    )


@router.get(
    "/vendor/orders",
    response_model=PaginatedResponse[VendorOrderItemResponse],
    status_code=status.HTTP_200_OK,
)
async def get_vendor_orders(
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
    current_user: User = Depends(require_vendor),
    order_service: OrderService = Depends(get_order_service),
):
    return await order_service.get_vendor_orders(
        user=current_user,
        page=page,
        size=size,
    )


@router.patch(
    "/vendor/orders/{order_item_id}/status",
    response_model=VendorOrderItemResponse,
    status_code=status.HTTP_200_OK,
)
async def update_vendor_order_item_status(
    order_item_id: uuid.UUID,
    payload: OrderStatusUpdate,
    current_user: User = Depends(require_vendor),
    order_service: OrderService = Depends(get_order_service),
):
    return await order_service.update_vendor_order_item_status(
        user=current_user,
        order_item_id=order_item_id,
        status=payload.status,
    )
