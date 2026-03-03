import uuid

from fastapi import APIRouter, Depends, Response, status

from app.dependencies.auth import get_current_user
from app.dependencies.cart import get_cart_service
from app.models.user import User
from app.schemas.cart import CartItemCreate, CartItemUpdate, CartResponse
from app.services.cart import CartService

router = APIRouter(prefix="/api/v1/cart", tags=["Cart"])


@router.get("", response_model=CartResponse, status_code=status.HTTP_200_OK)
async def get_cart(
    current_user: User = Depends(get_current_user),
    cart_service: CartService = Depends(get_cart_service),
):
    return await cart_service.get_cart(current_user)


@router.post("/items", status_code=status.HTTP_200_OK)
async def add_cart_item(
    payload: CartItemCreate,
    current_user: User = Depends(get_current_user),
    cart_service: CartService = Depends(get_cart_service),
):
    await cart_service.add_item(current_user, payload.product_id, payload.quantity)
    return {"detail": "Item added to cart"}


@router.put("/items/{product_id}", status_code=status.HTTP_200_OK)
async def update_cart_item(
    product_id: uuid.UUID,
    payload: CartItemUpdate,
    current_user: User = Depends(get_current_user),
    cart_service: CartService = Depends(get_cart_service),
):
    await cart_service.update_item(current_user, product_id, payload.quantity)
    return {"detail": "Cart item updated"}


@router.delete("/items/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_cart_item(
    product_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    cart_service: CartService = Depends(get_cart_service),
):
    await cart_service.remove_item(current_user, product_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
async def clear_cart(
    current_user: User = Depends(get_current_user),
    cart_service: CartService = Depends(get_cart_service),
):
    await cart_service.clear_cart(current_user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
