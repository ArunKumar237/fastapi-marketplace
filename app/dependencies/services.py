from app.dependencies.address import get_address_service
from app.dependencies.cart import get_cart_service
from app.dependencies.category import get_category_service
from app.dependencies.orders import get_order_service
from app.dependencies.product import get_product_service
from app.dependencies.product_image import get_product_image_service
from app.dependencies.review import get_review_service
from app.dependencies.store import get_store_service

__all__ = [
    "get_address_service",
    "get_cart_service",
    "get_category_service",
    "get_order_service",
    "get_product_image_service",
    "get_product_service",
    "get_review_service",
    "get_store_service",
]
