from fastapi import APIRouter, Depends
from redis.asyncio import from_url as redis_from_url
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_db

router = APIRouter()
settings = get_settings()


@router.get("/health", tags=["Health"])
async def health_check(db: AsyncSession = Depends(get_db)):
    status = {
        "status": "ok",
        "database": "unknown",
        "redis": "unknown",
    }

    # Check database connectivity
    try:
        await db.execute(text("SELECT 1"))
        status["database"] = "connected"
    except Exception:
        status["status"] = "error"
        status["database"] = "disconnected"

    # Check Redis connectivity
    redis = redis_from_url(settings.REDIS_URL, decode_responses=True)
    try:
        pong = await redis.ping()
        status["redis"] = "connected" if pong else "disconnected"
        if not pong:
            status["status"] = "error"
    except Exception:
        status["status"] = "error"
        status["redis"] = "disconnected"
    finally:
        await redis.aclose()

    return status
