import uuid
from decimal import Decimal
from typing import TYPE_CHECKING

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import BaseModel

if TYPE_CHECKING:
    from .category import Category
    from .store import Store


class Product(BaseModel):
    __tablename__ = "products"
    __table_args__ = (
        sa.CheckConstraint("price > 0", name="ck_products_price_gt_0"),
        sa.CheckConstraint("stock >= 0", name="ck_products_stock_gte_0"),
    )

    name: Mapped[str] = mapped_column(sa.String(255), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(sa.String(1000), nullable=True)
    price: Mapped[Decimal] = mapped_column(sa.Numeric(10, 2), nullable=False)
    stock: Mapped[int] = mapped_column(sa.Integer, nullable=False, default=0)
    store_id: Mapped[uuid.UUID] = mapped_column(
        sa.ForeignKey("stores.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    category_id: Mapped[uuid.UUID] = mapped_column(
        sa.ForeignKey("categories.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    is_active: Mapped[bool] = mapped_column(sa.Boolean, nullable=False, default=True)

    store: Mapped["Store"] = relationship("Store", back_populates="products")
    category: Mapped["Category"] = relationship("Category", back_populates="products")
