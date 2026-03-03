import uuid

from app.exceptions import BadRequestException, ConflictException, NotFoundException
from app.models.user import User
from app.repositories.address import AddressRepository
from app.schemas.address import AddressCreate, AddressUpdate


class AddressService:
    def __init__(self, address_repo: AddressRepository):
        self.address_repo = address_repo

    async def create_address(self, current_user: User, payload: AddressCreate):
        data = payload.model_dump()
        user_addresses = await self.address_repo.get_user_addresses(current_user.id)

        if not user_addresses:
            data["is_default"] = True
        elif data.get("is_default"):
            await self.address_repo.unset_default_addresses(current_user.id)

        return await self.address_repo.create_address(current_user.id, data)

    async def list_addresses(self, current_user: User):
        return await self.address_repo.get_user_addresses(current_user.id)

    async def update_address(
        self,
        current_user: User,
        address_id: uuid.UUID,
        payload: AddressUpdate,
    ):
        address = await self.address_repo.get_user_address_by_id(
            current_user.id, address_id
        )
        if not address:
            raise NotFoundException(
                detail="Address not found",
                error_code="ADDRESS_NOT_FOUND",
            )

        data = payload.model_dump(exclude_unset=True)
        if not data:
            return address

        if data.get("is_default") is True:
            await self.address_repo.unset_default_addresses(current_user.id)
        elif data.get("is_default") is False and address.is_default:
            raise BadRequestException(
                detail="Default address cannot be unset directly",
                error_code="DEFAULT_ADDRESS_REQUIRED",
            )

        return await self.address_repo.update_address(address, data)

    async def delete_address(self, current_user: User, address_id: uuid.UUID) -> None:
        address = await self.address_repo.get_user_address_by_id(
            current_user.id, address_id
        )
        if not address:
            raise NotFoundException(
                detail="Address not found",
                error_code="ADDRESS_NOT_FOUND",
            )

        is_used = await self.address_repo.is_address_used_in_orders(
            current_user.id, address.id
        )
        if is_used:
            raise ConflictException(
                detail="Address is used by existing orders and cannot be deleted",
                error_code="ADDRESS_IN_USE",
            )

        was_default = address.is_default
        await self.address_repo.delete_address(address)

        if was_default:
            promoted = await self.address_repo.get_most_recent_address(current_user.id)
            if promoted:
                await self.address_repo.update_address(promoted, {"is_default": True})
