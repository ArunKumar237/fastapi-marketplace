import uuid

from fastapi import UploadFile
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.exceptions import BadRequestException, ForbiddenException, NotFoundException
from app.models.product import Product
from app.models.product_image import ProductImage
from app.models.user import User
from app.repositories.store import StoreRepository
from app.schemas.product_image import ProductImageResponse
from app.utils.file_utils import delete_file, save_file, validate_image

UPLOAD_DIR = "uploads/products"


class ProductImageService:
    def __init__(self, db: AsyncSession, store_repo: StoreRepository):
        self.db = db
        self.store_repo = store_repo

    async def _get_owned_product(self, product_id: uuid.UUID, current_user: User) -> Product:
        vendor_store = await self.store_repo.get_by_owner_id(current_user.id)
        if not vendor_store:
            raise NotFoundException(
                detail="Store not found for vendor",
                error_code="VENDOR_STORE_NOT_FOUND",
            )

        result = await self.db.execute(select(Product).where(Product.id == product_id))
        product = result.scalar_one_or_none()
        if not product:
            raise NotFoundException(
                detail="Product not found",
                error_code="PRODUCT_NOT_FOUND",
            )

        if product.store_id != vendor_store.id:
            raise ForbiddenException(
                detail="You do not own this product",
                error_code="PRODUCT_OWNERSHIP_REQUIRED",
            )

        return product

    async def upload_image(
        self,
        product_id: uuid.UUID,
        file: UploadFile,
        is_primary: bool,
        sort_order: int,
        current_user: User,
    ) -> ProductImageResponse:
        await self._get_owned_product(product_id, current_user)

        file_url = None
        try:
            validate_image(file)
            file_url = save_file(file, UPLOAD_DIR)

            if is_primary:
                await self.db.execute(
                    update(ProductImage)
                    .where(ProductImage.product_id == product_id)
                    .values(is_primary=False)
                )

            image = ProductImage(
                product_id=product_id,
                image_url=file_url,
                is_primary=is_primary,
                sort_order=sort_order,
            )
            self.db.add(image)
            await self.db.commit()
            await self.db.refresh(image)
            return ProductImageResponse.model_validate(image)
        except ValueError as exc:
            if file_url:
                delete_file(file_url)
            await self.db.rollback()
            raise BadRequestException(
                detail=str(exc),
                error_code="INVALID_IMAGE_UPLOAD",
            )
        except Exception:
            if file_url:
                delete_file(file_url)
            await self.db.rollback()
            raise

    async def delete_image(self, image_id: uuid.UUID, current_user: User) -> None:
        vendor_store = await self.store_repo.get_by_owner_id(current_user.id)
        if not vendor_store:
            raise NotFoundException(
                detail="Store not found for vendor",
                error_code="VENDOR_STORE_NOT_FOUND",
            )

        result = await self.db.execute(
            select(ProductImage)
            .options(joinedload(ProductImage.product))
            .where(ProductImage.id == image_id)
        )
        image = result.scalar_one_or_none()
        if not image:
            raise NotFoundException(
                detail="Product image not found",
                error_code="PRODUCT_IMAGE_NOT_FOUND",
            )

        if image.product.store_id != vendor_store.id:
            raise ForbiddenException(
                detail="You do not own this product",
                error_code="PRODUCT_OWNERSHIP_REQUIRED",
            )

        image_url = image.image_url
        await self.db.delete(image)
        await self.db.commit()

        delete_file(image_url)
