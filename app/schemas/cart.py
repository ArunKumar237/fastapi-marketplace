import uuid
from decimal import Decimal

from pydantic import BaseModel, Field


class CartItemCreate(BaseModel):
    product_id: uuid.UUID
    quantity: int = Field(default=1, ge=1)


class CartItemUpdate(BaseModel):
    quantity: int = Field(ge=0)


class CartItemResponse(BaseModel):
    product_id: uuid.UUID
    product_name: str
    product_price: Decimal
    product_image: str | None
    quantity: int
    line_subtotal: Decimal
    available: bool


class CartResponse(BaseModel):
    items: list[CartItemResponse]
    cart_total: Decimal
