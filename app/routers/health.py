from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.database import get_db

router = APIRouter()


@router.get("/health", tags=["Health"])
async def health_check(db: AsyncSession = Depends(get_db)):
    status = {
        "status": "ok",
        "database": "unknown",
        "redis": "not_checked",  # placeholder for Phase 13
    }

    # Check database connectivity
    try:
        await db.execute(text("SELECT 1"))
        status["database"] = "connected"
    except Exception:
        status["status"] = "error"
        status["database"] = "disconnected"

    # Later: Redis check will go here

    return status