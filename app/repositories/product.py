import uuid
from decimal import Decimal

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.product import Product


class ProductRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, data: dict) -> Product:
        product = Product(**data)
        self.db.add(product)
        await self.db.commit()
        await self.db.refresh(product)
        return product

    async def get_by_id(
        self,
        product_id: uuid.UUID,
        include_inactive: bool = False,
    ) -> Product | None:
        query = (
            select(Product)
            .options(joinedload(Product.store), joinedload(Product.category))
            .where(Product.id == product_id)
        )
        if not include_inactive:
            query = query.where(Product.is_active.is_(True))

        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def list(
        self,
        page: int,
        size: int,
        category_id: uuid.UUID | None = None,
        store_id: uuid.UUID | None = None,
        min_price: Decimal | None = None,
        max_price: Decimal | None = None,
        search: str | None = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        include_inactive: bool = False,
    ) -> tuple[list[Product], int]:
        filters = []

        if not include_inactive:
            filters.append(Product.is_active.is_(True))

        if category_id:
            filters.append(Product.category_id == category_id)

        if store_id:
            filters.append(Product.store_id == store_id)

        if min_price is not None:
            filters.append(Product.price >= min_price)

        if max_price is not None:
            filters.append(Product.price <= max_price)

        if search:
            term = f"%{search.strip()}%"
            filters.append(
                or_(
                    Product.name.ilike(term),
                    Product.description.ilike(term),
                )
            )

        total_query = select(func.count(Product.id))
        if filters:
            total_query = total_query.where(*filters)
        total_result = await self.db.execute(total_query)
        total = total_result.scalar_one()

        query = select(Product).options(joinedload(Product.store), joinedload(Product.category))
        if filters:
            query = query.where(*filters)

        sort_fields = {
            "price": Product.price,
            "created_at": Product.created_at,
            "name": Product.name,
        }
        sort_column = sort_fields.get(sort_by, Product.created_at)
        sort_expr = sort_column.asc() if sort_order.lower() == "asc" else sort_column.desc()

        query = (
            query.order_by(sort_expr)
            .offset((page - 1) * size)
            .limit(size)
        )

        result = await self.db.execute(query)
        items = list(result.scalars().all())
        return items, total

    async def update(self, product: Product, data: dict) -> Product:
        for field, value in data.items():
            setattr(product, field, value)
        await self.db.commit()
        await self.db.refresh(product)
        return product
