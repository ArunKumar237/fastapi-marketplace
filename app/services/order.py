import logging
import random
import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import delete, select

from app.exceptions import BadRequestException, ForbiddenException, NotFoundException
from app.models.address import Address
from app.models.cart_item import CartItem
from app.models.product import Product
from app.models.user import User
from app.repositories.cart import CartRepository
from app.repositories.order import OrderItemRepository, OrderRepository
from app.repositories.store import StoreRepository
from app.schemas.order import (
    OrderDetailResponse,
    OrderItemResponse,
    OrderResponse,
    ShippingAddressResponse,
    VendorOrderItemResponse,
)
from app.schemas.pagination import PaginatedResponse
from app.tasks.email import send_order_confirmation, send_status_update

VALID_ORDER_STATUSES = {"pending", "confirmed", "shipped", "delivered", "cancelled"}
VALID_TRANSITIONS = {
    "pending": {"confirmed", "cancelled"},
    "confirmed": {"shipped", "cancelled"},
    "shipped": {"delivered"},
    "delivered": set(),
    "cancelled": set(),
}
logger = logging.getLogger(__name__)


def log_order_placement_event(
    order_id: str,
    user_email: str,
    timestamp: str,
    order_details: dict,
) -> None:
    message = (
        f"order_placement_event order_id={order_id} "
        f"user_email={user_email} timestamp={timestamp} details={order_details}"
    )
    logger.info(
        "background_task_start order_placement order_id=%s user_email=%s timestamp=%s",
        order_id,
        user_email,
        timestamp,
    )
    logger.info(message)
    print(message)
    logger.info(
        "background_task_end order_placement order_id=%s user_email=%s",
        order_id,
        user_email,
    )


class OrderService:
    def __init__(
        self,
        order_repo: OrderRepository,
        order_item_repo: OrderItemRepository,
        cart_repo: CartRepository,
        store_repo: StoreRepository,
    ):
        self.order_repo = order_repo
        self.order_item_repo = order_item_repo
        self.cart_repo = cart_repo
        self.store_repo = store_repo
        self.db = order_repo.db

    async def _generate_order_number(self) -> str:
        date_part = datetime.utcnow().strftime("%Y%m%d")
        for _ in range(10):
            suffix = f"{random.randint(0, 9999):04d}"
            order_number = f"ORD-{date_part}-{suffix}"
            existing = await self.order_repo.get_order_by_number(order_number)
            if not existing:
                return order_number
        raise BadRequestException(
            detail="Failed to generate unique order number",
            error_code="ORDER_NUMBER_GENERATION_FAILED",
        )

    def _validate_transition(self, current: str, target: str) -> None:
        if target not in VALID_ORDER_STATUSES:
            raise BadRequestException(
                detail="Invalid status",
                error_code="INVALID_STATUS",
            )

        if target not in VALID_TRANSITIONS.get(current, set()):
            raise BadRequestException(
                detail=f"Invalid status transition: {current} -> {target}",
                error_code="INVALID_STATUS_TRANSITION",
            )

    async def place_order(
        self, user: User, shipping_address_id: uuid.UUID
    ) -> OrderDetailResponse:
        try:
            cart_items = await self.cart_repo.get_cart_items(user.id)
            if not cart_items:
                raise BadRequestException(
                    detail="Cart is empty",
                    error_code="EMPTY_CART",
                )

            address_result = await self.db.execute(
                select(Address).where(
                    Address.id == shipping_address_id,
                    Address.user_id == user.id,
                )
            )
            address = address_result.scalar_one_or_none()
            if not address:
                raise BadRequestException(
                    detail="Invalid shipping address",
                    error_code="INVALID_SHIPPING_ADDRESS",
                )

            order_number = await self._generate_order_number()
            total_amount = Decimal("0")
            order_items_payload: list[dict] = []

            for cart_item in cart_items:
                product_result = await self.db.execute(
                    select(Product)
                    .where(Product.id == cart_item.product_id)
                    .with_for_update()
                )
                product = product_result.scalar_one_or_none()
                if not product:
                    raise NotFoundException(
                        detail="Product not found",
                        error_code="PRODUCT_NOT_FOUND",
                    )

                if not product.is_active:
                    raise BadRequestException(
                        detail=f"Product '{product.name}' is inactive",
                        error_code="INACTIVE_PRODUCT",
                    )

                if product.stock < cart_item.quantity:
                    raise BadRequestException(
                        detail=f"Insufficient stock for product '{product.name}'",
                        error_code="INSUFFICIENT_STOCK",
                    )

                unit_price = product.price
                subtotal = unit_price * cart_item.quantity
                total_amount += subtotal

                order_items_payload.append(
                    {
                        "product_id": product.id,
                        "store_id": product.store_id,
                        "quantity": cart_item.quantity,
                        "unit_price": unit_price,
                        "subtotal": subtotal,
                        "status": "pending",
                    }
                )

                product.stock -= cart_item.quantity

            order = await self.order_repo.create_order(
                user_id=user.id,
                shipping_address_id=shipping_address_id,
                total_amount=total_amount,
                order_number=order_number,
            )

            for payload in order_items_payload:
                payload["order_id"] = order.id

            await self.order_item_repo.create_order_items(order_items_payload)
            await self.db.execute(delete(CartItem).where(CartItem.user_id == user.id))
            await self.db.commit()
        except Exception:
            await self.db.rollback()
            raise

        order = await self.order_repo.get_order_by_id(order.id)
        order_response = self._to_order_detail_response(order)
        try:
            send_order_confirmation.delay(str(order_response.id), user.email)
        except Exception:
            logger.exception(
                "Failed to enqueue send_order_confirmation order_id=%s user_email=%s",
                order_response.id,
                user.email,
            )
        return order_response

    async def get_user_orders(
        self,
        user: User,
        page: int,
        size: int,
        status: str | None = None,
    ) -> PaginatedResponse[OrderResponse]:
        orders, total = await self.order_repo.get_user_orders(
            user_id=user.id,
            page=page,
            size=size,
            status=status,
        )
        items = [
            OrderResponse(
                id=order.id,
                order_number=order.order_number,
                status=order.status,
                total_amount=order.total_amount,
                created_at=order.created_at,
            )
            for order in orders
        ]
        return PaginatedResponse[OrderResponse](
            items=items,
            total=total,
            page=page,
            size=size,
        )

    async def get_user_order_detail(
        self, user: User, order_id: uuid.UUID
    ) -> OrderDetailResponse:
        order = await self.order_repo.get_order_by_id(order_id)
        if not order or order.user_id != user.id:
            raise NotFoundException(
                detail="Order not found",
                error_code="ORDER_NOT_FOUND",
            )
        return self._to_order_detail_response(order)

    async def get_vendor_orders(
        self,
        user: User,
        page: int,
        size: int,
    ) -> PaginatedResponse[VendorOrderItemResponse]:
        store = await self.store_repo.get_by_owner_id(user.id)
        if not store:
            raise NotFoundException(
                detail="Vendor store not found",
                error_code="VENDOR_STORE_NOT_FOUND",
            )

        items, total = await self.order_item_repo.get_vendor_order_items(
            store_id=store.id,
            page=page,
            size=size,
        )

        payload = [
            VendorOrderItemResponse(
                order_item_id=item.id,
                order_number=item.order.order_number,
                customer_name=item.order.user.full_name,
                product_name=item.product.name,
                quantity=item.quantity,
                item_status=item.status,
                created_at=item.created_at,
            )
            for item in items
        ]

        return PaginatedResponse[VendorOrderItemResponse](
            items=payload,
            total=total,
            page=page,
            size=size,
        )

    async def update_vendor_order_item_status(
        self,
        user: User,
        order_item_id: uuid.UUID,
        status: str,
    ) -> VendorOrderItemResponse:
        store = await self.store_repo.get_by_owner_id(user.id)
        if not store:
            raise NotFoundException(
                detail="Vendor store not found",
                error_code="VENDOR_STORE_NOT_FOUND",
            )

        try:
            order_item = await self.order_item_repo.get_order_item_by_id(order_item_id)
            if not order_item:
                raise NotFoundException(
                    detail="Order item not found",
                    error_code="ORDER_ITEM_NOT_FOUND",
                )

            if order_item.store_id != store.id:
                raise ForbiddenException(
                    detail="You do not have permission to update this order item",
                    error_code="ORDER_ITEM_FORBIDDEN",
                )

            self._validate_transition(order_item.status, status)
            await self.order_item_repo.update_item_status(order_item, status)

            sibling_items = await self.order_item_repo.get_order_items_by_order_id(
                order_item.order_id
            )
            if sibling_items and all(item.status == status for item in sibling_items):
                order = await self.order_repo.get_order_by_id(order_item.order_id)
                if (
                    order
                    and order.status in VALID_TRANSITIONS
                    and status in VALID_ORDER_STATUSES
                ):
                    if (
                        status in VALID_TRANSITIONS.get(order.status, set())
                        or order.status == status
                    ):
                        await self.order_repo.update_order_status(order, status)
            await self.db.commit()
        except Exception:
            await self.db.rollback()
            raise

        order_item = await self.order_item_repo.get_order_item_by_id(order_item_id)
        try:
            send_status_update.delay(
                str(order_item.order.id),
                order_item.order.user.email,
                order_item.status,
            )
        except Exception:
            logger.exception(
                "Failed to enqueue send_status_update order_id=%s user_email=%s status=%s",
                order_item.order.id,
                order_item.order.user.email,
                order_item.status,
            )
        return VendorOrderItemResponse(
            order_item_id=order_item.id,
            order_number=order_item.order.order_number,
            customer_name=order_item.order.user.full_name,
            product_name=order_item.product.name,
            quantity=order_item.quantity,
            item_status=order_item.status,
            created_at=order_item.created_at,
        )

    def _to_order_detail_response(self, order) -> OrderDetailResponse:
        return OrderDetailResponse(
            id=order.id,
            order_number=order.order_number,
            status=order.status,
            total_amount=order.total_amount,
            created_at=order.created_at,
            shipping_address=ShippingAddressResponse.model_validate(order.address),
            items=[
                OrderItemResponse(
                    product_id=item.product_id,
                    product_name=item.product.name,
                    quantity=item.quantity,
                    unit_price=item.unit_price,
                    subtotal=item.subtotal,
                    status=item.status,
                )
                for item in order.order_items
            ],
        )
