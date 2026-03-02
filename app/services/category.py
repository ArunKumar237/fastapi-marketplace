import re
import uuid

from app.exceptions import BadRequestException, ConflictException, NotFoundException
from app.models.category import Category
from app.repositories.category import CategoryRepository
from app.schemas.category import CategoryCreate, CategoryResponse, CategoryUpdate


class CategoryService:
    def __init__(self, category_repo: CategoryRepository):
        self.category_repo = category_repo

    def _to_category_response(self, category: Category) -> CategoryResponse:
        return CategoryResponse(
            id=category.id,
            name=category.name,
            slug=category.slug,
            description=category.description,
            is_active=category.is_active,
        )

    def _slugify(self, name: str) -> str:
        slug = name.strip().lower()
        slug = re.sub(r"[^a-z0-9\s-]", "", slug)
        slug = re.sub(r"[\s_-]+", "-", slug).strip("-")
        if not slug:
            raise BadRequestException(
                detail="Category name does not produce a valid slug",
                error_code="INVALID_CATEGORY_NAME",
            )
        return slug

    async def _generate_unique_slug(
        self,
        name: str,
        exclude_category_id: uuid.UUID | None = None,
    ) -> str:
        base_slug = self._slugify(name)
        slug = base_slug
        suffix = 1

        while True:
            existing = await self.category_repo.get_by_slug(slug)
            if not existing or (
                exclude_category_id is not None and existing.id == exclude_category_id
            ):
                break
            slug = f"{base_slug}-{suffix}"
            suffix += 1

        return slug

    async def create_category(self, data: CategoryCreate) -> CategoryResponse:
        existing = await self.category_repo.get_by_name(data.name)
        if existing:
            raise ConflictException(
                detail="Category name is already in use",
                error_code="CATEGORY_NAME_NOT_UNIQUE",
            )

        slug = await self._generate_unique_slug(data.name)
        category = await self.category_repo.create(
            {
                "name": data.name,
                "slug": slug,
                "description": data.description,
                "is_active": data.is_active,
            }
        )
        return self._to_category_response(category)

    async def update_category(
        self,
        category_id: uuid.UUID,
        data: CategoryUpdate,
    ) -> CategoryResponse:
        category = await self.category_repo.get_by_id(category_id)
        if not category:
            raise NotFoundException(
                detail="Category not found",
                error_code="CATEGORY_NOT_FOUND",
            )

        update_data = data.model_dump(exclude_unset=True)
        if not update_data:
            return self._to_category_response(category)

        new_name = update_data.get("name")
        if new_name and new_name != category.name:
            existing = await self.category_repo.get_by_name(new_name)
            if existing:
                raise ConflictException(
                    detail="Category name is already in use",
                    error_code="CATEGORY_NAME_NOT_UNIQUE",
                )
            update_data["slug"] = await self._generate_unique_slug(
                new_name,
                exclude_category_id=category.id,
            )

        updated = await self.category_repo.update(category, update_data)
        return self._to_category_response(updated)

    async def list_categories(self) -> list[CategoryResponse]:
        categories = await self.category_repo.list_active()
        return [self._to_category_response(category) for category in categories]

    async def get_category(self, category_id: uuid.UUID) -> CategoryResponse:
        category = await self.category_repo.get_by_id(category_id)
        if not category:
            raise NotFoundException(
                detail="Category not found",
                error_code="CATEGORY_NOT_FOUND",
            )
        return self._to_category_response(category)

    async def delete_category(self, category_id: uuid.UUID) -> None:
        category = await self.category_repo.get_by_id(category_id)
        if not category:
            raise NotFoundException(
                detail="Category not found",
                error_code="CATEGORY_NOT_FOUND",
            )

        await self.category_repo.delete(category)
