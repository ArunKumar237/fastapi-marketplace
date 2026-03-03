import uuid
from typing import TYPE_CHECKING

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import BaseModel

if TYPE_CHECKING:
    from .product import Product
    from .user import User


class Review(BaseModel):
    __tablename__ = "reviews"
    __table_args__ = (
        sa.CheckConstraint("rating >= 1 AND rating <= 5", name="ck_reviews_rating_between_1_and_5"),
        sa.UniqueConstraint("user_id", "product_id", name="uq_reviews_user_product"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        sa.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    product_id: Mapped[uuid.UUID] = mapped_column(
        sa.ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    rating: Mapped[int] = mapped_column(sa.Integer, nullable=False)
    comment: Mapped[str | None] = mapped_column(sa.Text, nullable=True)

    user: Mapped["User"] = relationship("User", back_populates="reviews")
    product: Mapped["Product"] = relationship("Product", back_populates="reviews")
