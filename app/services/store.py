import uuid

from app.exceptions import ConflictException, ForbiddenException, NotFoundException
from app.models.store import Store
from app.models.user import User, UserRole
from app.repositories.store import StoreRepository
from app.schemas.store import StoreCreate, StoreResponse, StoreUpdate


class StoreService:
    def __init__(self, store_repo: StoreRepository):
        self.store_repo = store_repo

    def _to_store_response(self, store: Store) -> StoreResponse:
        return StoreResponse(
            id=store.id,
            name=store.name,
            description=store.description,
            is_active=store.is_active,
            owner_id=store.owner_id,
            owner=store.owner,
            product_count=store.product_count,
        )

    async def create_store(
        self, current_user: User, store_data: StoreCreate
    ) -> StoreResponse:
        if current_user.role != UserRole.VENDOR:
            raise ForbiddenException(
                detail="Only vendors can create stores",
                error_code="VENDOR_ROLE_REQUIRED",
            )

        existing_vendor_store = await self.store_repo.get_by_owner_id(current_user.id)
        if existing_vendor_store:
            raise ConflictException(
                detail="Vendor already has a store",
                error_code="STORE_ALREADY_EXISTS_FOR_VENDOR",
            )

        existing_store_name = await self.store_repo.get_by_name(store_data.name)
        if existing_store_name:
            raise ConflictException(
                detail="Store name is already in use",
                error_code="STORE_NAME_NOT_UNIQUE",
            )

        store = await self.store_repo.create(
            {
                "name": store_data.name,
                "description": store_data.description,
                "product_count": store_data.product_count,
                "owner_id": current_user.id,
            }
        )
        store = await self.store_repo.get_by_id(store.id)
        return self._to_store_response(store)

    async def list_stores(
        self,
        page: int,
        size: int,
        include_inactive: bool = False,
    ) -> tuple[list[StoreResponse], int]:
        stores, total = await self.store_repo.list(
            page=page,
            size=size,
            active_only=not include_inactive,
        )
        return [self._to_store_response(store) for store in stores], total

    async def get_store_public_profile(self, store_id: uuid.UUID) -> StoreResponse:
        store = await self.store_repo.get_by_id(store_id)
        if not store or not store.is_active:
            raise NotFoundException(
                detail="Store not found",
                error_code="STORE_NOT_FOUND",
            )
        return self._to_store_response(store)

    async def check_ownership(self, store_id: uuid.UUID, user_id: uuid.UUID) -> Store:
        store = await self.store_repo.get_by_id(store_id)
        if not store:
            raise NotFoundException(
                detail="Store not found",
                error_code="STORE_NOT_FOUND",
            )

        if store.owner_id != user_id:
            raise ForbiddenException(
                detail="You do not own this store",
                error_code="STORE_OWNERSHIP_REQUIRED",
            )
        return store

    async def update_store(
        self,
        store_id: uuid.UUID,
        current_user: User,
        updates: StoreUpdate,
    ) -> StoreResponse:
        store = await self.check_ownership(store_id, current_user.id)
        update_data = updates.model_dump(exclude_unset=True)

        if not update_data:
            return self._to_store_response(store)

        new_name = update_data.get("name")
        if new_name and new_name != store.name:
            existing_store_name = await self.store_repo.get_by_name(new_name)
            if existing_store_name:
                raise ConflictException(
                    detail="Store name is already in use",
                    error_code="STORE_NAME_NOT_UNIQUE",
                )

        updated_store = await self.store_repo.update(store, update_data)
        updated_store = await self.store_repo.get_by_id(updated_store.id)
        return self._to_store_response(updated_store)

    async def update_store_status(
        self, store_id: uuid.UUID, is_active: bool
    ) -> StoreResponse:
        store = await self.store_repo.get_by_id(store_id)
        if not store:
            raise NotFoundException(
                detail="Store not found",
                error_code="STORE_NOT_FOUND",
            )

        updated_store = await self.store_repo.update(store, {"is_active": is_active})
        updated_store = await self.store_repo.get_by_id(updated_store.id)
        return self._to_store_response(updated_store)

    async def delete_store(self, store_id: uuid.UUID) -> None:
        store = await self.store_repo.get_by_id(store_id)
        if not store:
            raise NotFoundException(
                detail="Store not found",
                error_code="STORE_NOT_FOUND",
            )
        await self.store_repo.delete(store)
