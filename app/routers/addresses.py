import uuid

from app.dependencies.address import get_address_service
from fastapi import APIRouter, Depends, Response, status

from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.address import AddressCreate, AddressResponse, AddressUpdate
from app.services.address import AddressService

router = APIRouter(prefix="/api/v1/me/addresses", tags=["Addresses"])


@router.post("", response_model=AddressResponse, status_code=status.HTTP_201_CREATED)
async def create_address(
    payload: AddressCreate,
    current_user: User = Depends(get_current_user),
    address_service: AddressService = Depends(get_address_service),
):
    return await address_service.create_address(current_user, payload)


@router.get("", response_model=list[AddressResponse], status_code=status.HTTP_200_OK)
async def list_addresses(
    current_user: User = Depends(get_current_user),
    address_service: AddressService = Depends(get_address_service),
):
    return await address_service.list_addresses(current_user)


@router.put(
    "/{address_id}", response_model=AddressResponse, status_code=status.HTTP_200_OK
)
async def update_address(
    address_id: uuid.UUID,
    payload: AddressUpdate,
    current_user: User = Depends(get_current_user),
    address_service: AddressService = Depends(get_address_service),
):
    return await address_service.update_address(current_user, address_id, payload)


@router.delete("/{address_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_address(
    address_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    address_service: AddressService = Depends(get_address_service),
):
    await address_service.delete_address(current_user, address_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
