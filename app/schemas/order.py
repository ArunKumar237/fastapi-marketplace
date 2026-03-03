import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel


class OrderCreate(BaseModel):
    shipping_address_id: uuid.UUID


class OrderItemResponse(BaseModel):
    product_id: uuid.UUID
    product_name: str
    quantity: int
    unit_price: Decimal
    subtotal: Decimal
    status: str


class ShippingAddressResponse(BaseModel):
    id: uuid.UUID
    line1: str | None = None
    line2: str | None = None
    city: str | None = None
    state: str | None = None
    postal_code: str | None = None
    country: str | None = None

    model_config = {"from_attributes": True}


class OrderResponse(BaseModel):
    id: uuid.UUID
    order_number: str
    status: str
    total_amount: Decimal
    created_at: datetime


class OrderDetailResponse(BaseModel):
    id: uuid.UUID
    order_number: str
    status: str
    total_amount: Decimal
    created_at: datetime
    shipping_address: ShippingAddressResponse
    items: list[OrderItemResponse]


class OrderStatusUpdate(BaseModel):
    status: str


class VendorOrderItemResponse(BaseModel):
    order_item_id: uuid.UUID
    order_number: str
    customer_name: str
    product_name: str
    quantity: int
    item_status: str
    created_at: datetime
