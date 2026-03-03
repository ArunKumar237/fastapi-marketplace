import uuid
from typing import TYPE_CHECKING

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import BaseModel

if TYPE_CHECKING:
    from .product import Product
    from .user import User


class CartItem(BaseModel):
    __tablename__ = "cart_items"
    __table_args__ = (
        sa.UniqueConstraint("user_id", "product_id", name="uq_cart_items_user_product"),
        sa.CheckConstraint("quantity > 0", name="ck_cart_items_quantity_gt_0"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        sa.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    product_id: Mapped[uuid.UUID] = mapped_column(
        sa.ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
    )
    quantity: Mapped[int] = mapped_column(sa.Integer, nullable=False, default=1)

    user: Mapped["User"] = relationship("User", back_populates="cart_items")
    product: Mapped["Product"] = relationship("Product", back_populates="cart_items")
