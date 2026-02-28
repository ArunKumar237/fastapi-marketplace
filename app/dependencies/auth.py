# app/dependencies/auth.py

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.exceptions import UnauthorizedException  # ← use the real one
from app.models.user import User
from app.repositories.user import UserRepository
from app.services.auth import decode_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")
oauth2_scheme_optional = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/login",
    auto_error=False,
)


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:

    payload = decode_token(token)
    if not payload:
        raise UnauthorizedException(
            detail="Invalid or expired token",
            error_code="INVALID_TOKEN",
        )

    if payload.get("type") != "access":
        raise UnauthorizedException(
            detail="Invalid token type",
            error_code="INVALID_TOKEN_TYPE",
        )

    user_id = payload.get("sub")
    if not user_id:
        raise UnauthorizedException(
            detail="Invalid token payload",
            error_code="INVALID_TOKEN_PAYLOAD",
        )

    user_repo = UserRepository(db)
    user = await user_repo.get_by_id(user_id)

    if not user:
        raise UnauthorizedException(
            detail="User not found",
            error_code="USER_NOT_FOUND",
        )

    if not user.is_active:
        raise UnauthorizedException(
            detail="Inactive account",
            error_code="INACTIVE_ACCOUNT",
        )

    return user


async def get_current_user_optional(
    token: str | None = Depends(oauth2_scheme_optional),
    db: AsyncSession = Depends(get_db),
) -> User | None:
    if not token:
        return None

    payload = decode_token(token)
    if not payload or payload.get("type") != "access":
        return None

    user_id = payload.get("sub")
    if not user_id:
        return None

    user_repo = UserRepository(db)
    user = await user_repo.get_by_id(user_id)
    if not user or not user.is_active:
        return None

    return user
