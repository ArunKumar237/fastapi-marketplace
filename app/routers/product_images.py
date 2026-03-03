import uuid

from fastapi import APIRouter, Depends, File, Form, Response, UploadFile, status

from app.dependencies.product_image import get_product_image_service
from app.dependencies.roles import require_vendor
from app.models.user import User
from app.schemas.product_image import ProductImageResponse
from app.services.product_image import ProductImageService

router = APIRouter(prefix="/api/v1", tags=["Product Images"])


@router.post(
    "/products/{product_id}/images",
    response_model=ProductImageResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_product_image(
    product_id: uuid.UUID,
    file: UploadFile = File(...),
    is_primary: bool = Form(False),
    sort_order: int = Form(0, ge=0),
    current_user: User = Depends(require_vendor),
    service: ProductImageService = Depends(get_product_image_service),
):
    return await service.upload_image(
        product_id=product_id,
        file=file,
        is_primary=is_primary,
        sort_order=sort_order,
        current_user=current_user,
    )


@router.delete("/product-images/{image_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product_image(
    image_id: uuid.UUID,
    current_user: User = Depends(require_vendor),
    service: ProductImageService = Depends(get_product_image_service),
):
    await service.delete_image(image_id=image_id, current_user=current_user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
