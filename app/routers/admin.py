from fastapi import APIRouter, Depends, status

from app.dependencies.roles import require_admin
from app.models.user import User

router = APIRouter(prefix="/api/v1/admin", tags=["Admin"])


@router.get("/health", status_code=status.HTTP_200_OK)
async def admin_health(_: User = Depends(require_admin)):
    return {"status": "ok", "scope": "admin"}
