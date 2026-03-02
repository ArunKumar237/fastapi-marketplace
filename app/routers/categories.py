import uuid

from fastapi import APIRouter, Depends, Response, status

from app.dependencies.category import get_category_service
from app.dependencies.roles import require_admin
from app.models.user import User
from app.schemas.category import CategoryCreate, CategoryResponse, CategoryUpdate
from app.services.category import CategoryService

router = APIRouter(prefix="/api/v1/categories", tags=["Categories"])


@router.get("", response_model=list[CategoryResponse], status_code=status.HTTP_200_OK)
async def list_categories(
    category_service: CategoryService = Depends(get_category_service),
):
    return await category_service.list_categories()


@router.post("", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_category(
    category_data: CategoryCreate,
    _: User = Depends(require_admin),
    category_service: CategoryService = Depends(get_category_service),
):
    return await category_service.create_category(category_data)


@router.put(
    "/{category_id}",
    response_model=CategoryResponse,
    status_code=status.HTTP_200_OK,
)
async def update_category(
    category_id: uuid.UUID,
    category_data: CategoryUpdate,
    _: User = Depends(require_admin),
    category_service: CategoryService = Depends(get_category_service),
):
    return await category_service.update_category(category_id, category_data)


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(
    category_id: uuid.UUID,
    _: User = Depends(require_admin),
    category_service: CategoryService = Depends(get_category_service),
):
    await category_service.delete_category(category_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
