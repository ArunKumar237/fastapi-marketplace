# app/dependencies/auth.py

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db  # adjust if needed
from app.models.user import User
from app.repositories.user import UserRepository
from app.services.auth import decode_token

# OAuth2 scheme (extracts Bearer token from header)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


class UnauthorizedException(Exception):
    pass


# =====================================================
# GET CURRENT USER DEPENDENCY
# =====================================================


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:

    # 1 Decode token
    payload = decode_token(token)
    if not payload:
        raise UnauthorizedException("Invalid or expired token")

    # 2 Ensure token type is access
    if payload.get("type") != "access":
        raise UnauthorizedException("Invalid token type")

    # 3 Extract user ID
    user_id = payload.get("sub")
    if not user_id:
        raise UnauthorizedException("Invalid token payload")

    # 4 Load user from DB
    user_repo = UserRepository(db)
    user = await user_repo.get_by_id(user_id)

    if not user:
        raise UnauthorizedException("User not found")

    # 5 Check active
    if not user.is_active:
        raise UnauthorizedException("Inactive account")

    return user
