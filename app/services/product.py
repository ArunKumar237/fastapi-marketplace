import uuid
from decimal import Decimal

from app.exceptions import ForbiddenException, NotFoundException
from app.models.product import Product
from app.models.user import User
from app.repositories.category import CategoryRepository
from app.repositories.product import ProductRepository
from app.repositories.review import ReviewRepository
from app.repositories.store import StoreRepository
from app.schemas.pagination import PaginatedResponse
from app.schemas.product import (
    ProductCreate,
    ProductListResponse,
    ProductResponse,
    ProductUpdate,
)


class ProductService:
    def __init__(
        self,
        product_repo: ProductRepository,
        store_repo: StoreRepository,
        category_repo: CategoryRepository,
        review_repo: ReviewRepository,
    ):
        self.product_repo = product_repo
        self.store_repo = store_repo
        self.category_repo = category_repo
        self.review_repo = review_repo

    async def _to_product_response(self, product: Product) -> ProductResponse:
        average_rating, review_count = await self.review_repo.get_review_aggregates(
            product.id
        )
        return ProductResponse(
            id=product.id,
            name=product.name,
            description=product.description,
            price=product.price,
            stock=product.stock,
            is_active=product.is_active,
            store=product.store,
            category=product.category,
            images=product.images,
            average_rating=average_rating,
            review_count=review_count,
            created_at=product.created_at,
            updated_at=product.updated_at,
        )

    async def _to_product_list_response(self, product: Product) -> ProductListResponse:
        average_rating, review_count = await self.review_repo.get_review_aggregates(
            product.id
        )
        return ProductListResponse(
            id=product.id,
            name=product.name,
            description=product.description,
            price=product.price,
            stock=product.stock,
            is_active=product.is_active,
            store=product.store,
            category=product.category,
            images=product.images,
            average_rating=average_rating,
            review_count=review_count,
            created_at=product.created_at,
            updated_at=product.updated_at,
        )

    async def _get_vendor_store(self, current_user: User):
        store = await self.store_repo.get_by_owner_id(current_user.id)
        if not store:
            raise NotFoundException(
                detail="Store not found for vendor",
                error_code="VENDOR_STORE_NOT_FOUND",
            )
        return store

    async def create_product(
        self,
        current_user: User,
        data: ProductCreate,
    ) -> ProductResponse:
        store = await self._get_vendor_store(current_user)

        category = await self.category_repo.get_by_id(data.category_id)
        if not category:
            raise NotFoundException(
                detail="Category not found",
                error_code="CATEGORY_NOT_FOUND",
            )

        product = await self.product_repo.create(
            {
                "name": data.name,
                "description": data.description,
                "price": data.price,
                "stock": data.stock,
                "store_id": store.id,
                "category_id": data.category_id,
                "is_active": True,
            }
        )

        product = await self.product_repo.get_by_id(product.id, include_inactive=True)
        return await self._to_product_response(product)

    async def list_products(
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
    ) -> PaginatedResponse[ProductListResponse]:
        items, total = await self.product_repo.list(
            page=page,
            size=size,
            category_id=category_id,
            store_id=store_id,
            min_price=min_price,
            max_price=max_price,
            search=search,
            sort_by=sort_by,
            sort_order=sort_order,
            include_inactive=include_inactive,
        )
        return PaginatedResponse[ProductListResponse](
            items=[await self._to_product_list_response(item) for item in items],
            total=total,
            page=page,
            size=size,
        )

    async def get_product(
        self,
        product_id: uuid.UUID,
        current_user: User | None = None,
    ) -> ProductResponse:
        product = await self.product_repo.get_by_id(product_id, include_inactive=True)
        if not product:
            raise NotFoundException(
                detail="Product not found",
                error_code="PRODUCT_NOT_FOUND",
            )

        if not product.is_active:
            if not current_user:
                raise NotFoundException(
                    detail="Product not found",
                    error_code="PRODUCT_NOT_FOUND",
                )

            store = await self.store_repo.get_by_owner_id(current_user.id)
            if not store or store.id != product.store_id:
                raise NotFoundException(
                    detail="Product not found",
                    error_code="PRODUCT_NOT_FOUND",
                )

        return await self._to_product_response(product)

    async def update_product(
        self,
        product_id: uuid.UUID,
        current_user: User,
        data: ProductUpdate,
    ) -> ProductResponse:
        store = await self._get_vendor_store(current_user)

        product = await self.product_repo.get_by_id(product_id, include_inactive=True)
        if not product:
            raise NotFoundException(
                detail="Product not found",
                error_code="PRODUCT_NOT_FOUND",
            )

        if product.store_id != store.id:
            raise ForbiddenException(
                detail="You do not own this product",
                error_code="PRODUCT_OWNERSHIP_REQUIRED",
            )

        update_data = data.model_dump(exclude_unset=True)
        if "category_id" in update_data:
            category = await self.category_repo.get_by_id(update_data["category_id"])
            if not category:
                raise NotFoundException(
                    detail="Category not found",
                    error_code="CATEGORY_NOT_FOUND",
                )

        if not update_data:
            return await self._to_product_response(product)

        updated = await self.product_repo.update(product, update_data)
        updated = await self.product_repo.get_by_id(updated.id, include_inactive=True)
        return await self._to_product_response(updated)

    async def delete_product(
        self,
        product_id: uuid.UUID,
        current_user: User,
    ) -> None:
        store = await self._get_vendor_store(current_user)

        product = await self.product_repo.get_by_id(product_id, include_inactive=True)
        if not product:
            raise NotFoundException(
                detail="Product not found",
                error_code="PRODUCT_NOT_FOUND",
            )

        if product.store_id != store.id:
            raise ForbiddenException(
                detail="You do not own this product",
                error_code="PRODUCT_OWNERSHIP_REQUIRED",
            )

        await self.product_repo.update(product, {"is_active": False})
