from typing import TYPE_CHECKING

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import BaseModel

if TYPE_CHECKING:
    from .product import Product


class Category(BaseModel):
    __tablename__ = "categories"

    name: Mapped[str] = mapped_column(sa.String(50), unique=True, nullable=False)
    slug: Mapped[str] = mapped_column(
        sa.String(60),
        unique=True,
        nullable=False,
        index=True,
    )
    description: Mapped[str | None] = mapped_column(sa.String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(sa.Boolean, default=True, nullable=False)
    products: Mapped[list["Product"]] = relationship(
        "Product",
        back_populates="category",
    )
