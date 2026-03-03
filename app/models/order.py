import uuid
from decimal import Decimal
from typing import TYPE_CHECKING

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import BaseModel

if TYPE_CHECKING:
    from .address import Address
    from .order_item import OrderItem
    from .user import User


class Order(BaseModel):
    __tablename__ = "orders"

    user_id: Mapped[uuid.UUID] = mapped_column(
        sa.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    shipping_address_id: Mapped[uuid.UUID] = mapped_column(
        sa.ForeignKey("addresses.id", ondelete="RESTRICT"),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(sa.String(20), nullable=False, default="pending")
    total_amount: Mapped[Decimal] = mapped_column(sa.Numeric(12, 2), nullable=False)
    order_number: Mapped[str] = mapped_column(sa.String(20), nullable=False, unique=True)

    user: Mapped["User"] = relationship("User", back_populates="orders")
    address: Mapped["Address"] = relationship("Address", back_populates="orders")
    order_items: Mapped[list["OrderItem"]] = relationship(
        "OrderItem",
        back_populates="order",
        cascade="all, delete-orphan",
    )
