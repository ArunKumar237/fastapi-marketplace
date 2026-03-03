import uuid
from typing import TYPE_CHECKING

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import BaseModel

if TYPE_CHECKING:
    from .order import Order
    from .user import User


class Address(BaseModel):
    __tablename__ = "addresses"

    user_id: Mapped[uuid.UUID] = mapped_column(
        sa.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    line1: Mapped[str] = mapped_column(sa.String(255), nullable=False)
    line2: Mapped[str | None] = mapped_column(sa.String(255), nullable=True)
    city: Mapped[str] = mapped_column(sa.String(100), nullable=False)
    state: Mapped[str] = mapped_column(sa.String(100), nullable=False)
    postal_code: Mapped[str] = mapped_column(sa.String(20), nullable=False)
    country: Mapped[str] = mapped_column(sa.String(100), nullable=False)
    is_default: Mapped[bool] = mapped_column(sa.Boolean, nullable=False, default=False)

    user: Mapped["User"] = relationship("User", back_populates="addresses")
    orders: Mapped[list["Order"]] = relationship("Order", back_populates="address")
