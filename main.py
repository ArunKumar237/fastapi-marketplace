from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import get_settings
from app.database import engine
from app.exception_handler import register_exception_handlers
from app.routers.auth import router as auth_router
from app.routers.health import router as health_router

settings = get_settings()


# Lifespan handler (modern replacement for startup/shutdown events)
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    print("Starting application...")

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

# Register exception handlers
register_exception_handlers(app)

# Include routers
app.include_router(health_router, prefix="/api/v1")
app.include_router(auth_router)
