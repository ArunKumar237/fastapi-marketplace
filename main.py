import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.config import get_settings
from app.database import engine, ensure_database_schema
from app.exception_handler import register_exception_handlers
from app.routers.addresses import router as addresses_router
from app.routers.auth import router as auth_router
from app.routers.cart import router as cart_router
from app.routers.categories import router as categories_router
from app.routers.health import router as health_router
from app.routers.orders import router as orders_router
from app.routers.product_images import router as product_images_router
from app.routers.products import router as products_router
from app.routers.reviews import router as reviews_router
from app.routers.stores import router as stores_router
from app.websockets.orders import router as websocket_orders_router

settings = get_settings()
logger = logging.getLogger(__name__)


# Lifespan handler (modern replacement for startup/shutdown events)
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    print("Starting application...")
    await ensure_database_schema()
    logger.info("Database schema verified (missing tables created if needed).")

    yield

    # Shutdown logic
    print("Shutting down application...")
    await engine.dispose()  # Properly close DB connections


# Create FastAPI app
app = FastAPI(
    title="My FastAPI Service",
    description="Production-ready FastAPI backend with async SQLAlchemy",
    version="1.0.0",
    debug=settings.DEBUG,
    lifespan=lifespan,
)
os.makedirs("uploads", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Register exception handlers
register_exception_handlers(app)

# Include routers
app.include_router(health_router, prefix="/api/v1")
app.include_router(auth_router)
app.include_router(stores_router)
app.include_router(categories_router)
app.include_router(products_router)
app.include_router(reviews_router)
app.include_router(product_images_router)
app.include_router(cart_router)
app.include_router(addresses_router)
app.include_router(orders_router)
app.include_router(websocket_orders_router)
