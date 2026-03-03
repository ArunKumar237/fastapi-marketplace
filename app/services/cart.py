import uuid
from decimal import Decimal

from app.exceptions import BadRequestException, NotFoundException
from app.models.user import User
from app.repositories.cart import CartRepository
from app.repositories.product import ProductRepository
from app.schemas.cart import CartItemResponse, CartResponse


class CartService:
    def __init__(self, cart_repo: CartRepository, product_repo: ProductRepository):
        self.cart_repo = cart_repo
        self.product_repo = product_repo

    def _get_primary_image(self, product) -> str | None:
        if not product.images:
            return None
        primary = next((img for img in product.images if img.is_primary), None)
        if primary:
            return primary.image_url
        return product.images[0].image_url

    def _is_available(self, product, quantity: int) -> bool:
        if not product.is_active:
            return False
        if product.stock <= 0:
            return False
        if quantity > product.stock:
            return False
        return True

    async def add_item(self, user: User, product_id: uuid.UUID, quantity: int) -> None:
        if quantity <= 0:
            raise BadRequestException(
                detail="Quantity must be greater than 0",
                error_code="INVALID_QUANTITY",
            )

        product = await self.product_repo.get_by_id(product_id, include_inactive=True)
        if not product:
            raise NotFoundException(
                detail="Product not found",
                error_code="PRODUCT_NOT_FOUND",
            )

        if not product.is_active:
            raise BadRequestException(
                detail="Cannot add inactive product to cart",
                error_code="PRODUCT_INACTIVE",
            )

        cart_item = await self.cart_repo.get_cart_item(user.id, product_id)
        target_quantity = quantity if not cart_item else cart_item.quantity + quantity

        if target_quantity > product.stock:
            raise BadRequestException(
                detail="Requested quantity exceeds available stock",
                error_code="INSUFFICIENT_STOCK",
            )

        if cart_item:
            await self.cart_repo.update_cart_item_quantity(cart_item, target_quantity)
            return

        await self.cart_repo.create_cart_item(user.id, product_id, quantity)

    async def update_item(self, user: User, product_id: uuid.UUID, quantity: int) -> None:
        cart_item = await self.cart_repo.get_cart_item(user.id, product_id)
        if not cart_item:
            raise NotFoundException(
                detail="Cart item not found",
                error_code="CART_ITEM_NOT_FOUND",
            )

        if quantity < 0:
            raise BadRequestException(
                detail="Quantity must be 0 or greater",
                error_code="INVALID_QUANTITY",
            )

        if quantity == 0:
            await self.cart_repo.delete_cart_item(cart_item)
            return

        product = cart_item.product
        if not product:
            raise NotFoundException(
                detail="Product not found",
                error_code="PRODUCT_NOT_FOUND",
            )

        if quantity > product.stock:
            raise BadRequestException(
                detail="Requested quantity exceeds available stock",
                error_code="INSUFFICIENT_STOCK",
            )

        await self.cart_repo.update_cart_item_quantity(cart_item, quantity)

    async def remove_item(self, user: User, product_id: uuid.UUID) -> None:
        cart_item = await self.cart_repo.get_cart_item(user.id, product_id)
        if not cart_item:
            raise NotFoundException(
                detail="Cart item not found",
                error_code="CART_ITEM_NOT_FOUND",
            )
        await self.cart_repo.delete_cart_item(cart_item)

    async def clear_cart(self, user: User) -> None:
        await self.cart_repo.clear_cart(user.id)

    async def get_cart(self, user: User) -> CartResponse:
        cart_items = await self.cart_repo.get_cart_items(user.id)

        items: list[CartItemResponse] = []
        cart_total = Decimal("0")

        for cart_item in cart_items:
            product = cart_item.product
            if not product:
                continue

            line_subtotal = product.price * cart_item.quantity
            cart_total += line_subtotal

            items.append(
                CartItemResponse(
                    product_id=product.id,
                    product_name=product.name,
                    product_price=product.price,
                    product_image=self._get_primary_image(product),
                    quantity=cart_item.quantity,
                    line_subtotal=line_subtotal,
                    available=self._is_available(product, cart_item.quantity),
                )
            )

        return CartResponse(items=items, cart_total=cart_total)
