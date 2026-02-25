# app/routers/auth.py

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies.auth import get_current_user
from app.dependencies.roles import (
    require_admin,
    require_vendor,
    require_vendor_or_admin,
)
from app.exceptions import (
    BadRequestException,
    ForbiddenException,
    UnauthorizedException,
)
from app.models.user import User
from app.repositories.user import UserRepository
from app.schemas.user import (
    TokenResponse,
    UserCreate,
    UserLogin,
    UserResponse,
    UserUpdate,
)
from app.services.auth import create_access_token, decode_token
from app.services.user import UserService

router = APIRouter(prefix="/api/v1/auth", tags=["Auth"])


# =====================================================
# REGISTER
# =====================================================
@router.post("/register", response_model=UserResponse, status_code=201)
async def register(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db),
):
    user_repo = UserRepository(db)
    user_service = UserService(user_repo)

    try:
        user = await user_service.register(user_data)
        return user
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


# =====================================================
# LOGIN
# =====================================================
@router.post("/login", response_model=TokenResponse)
async def login(
    login_data: UserLogin,
    db: AsyncSession = Depends(get_db),
):
    user_repo = UserRepository(db)
    user_service = UserService(user_repo)

    try:
        tokens = await user_service.authenticate(
            login_data.email,
            login_data.password,
        )
        return tokens
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )


# =====================================================
# REFRESH TOKEN
# =====================================================
@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    refresh_token: str,
    db: AsyncSession = Depends(get_db),
):
    payload = decode_token(refresh_token)

    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    user_id = payload.get("sub")
    role = payload.get("role")

    if not user_id or not role:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    new_access_token = create_access_token(uuid.UUID(user_id), role)

    return {
        "access_token": new_access_token,
        "refresh_token": refresh_token,
    }


# =====================================================
# GET PROFILE (Protected)
# =====================================================
@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user


# =====================================================
# UPDATE PROFILE (Protected)
# =====================================================
@router.put("/me", response_model=UserResponse)
async def update_me(
    updates: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Build a dict of only the fields the client actually sent
    update_data = updates.model_dump(exclude_unset=True)

    if not update_data:
        raise BadRequestException(
            detail="No fields to update",
            error_code="EMPTY_UPDATE",
        )

    user_repo = UserRepository(db)
    updated_user = await user_repo.update(current_user, update_data)
    return updated_user


# =====================================================
# TEMPORARY TEST ROUTES — verify role enforcement
# Remove these once real admin/vendor endpoints exist
# =====================================================
@router.get("/test/admin-only", response_model=UserResponse)
async def test_admin_only(
    current_user: User = Depends(require_admin),
):
    """Only accessible with an admin token."""
    return current_user


@router.get("/test/vendor-only", response_model=UserResponse)
async def test_vendor_only(
    current_user: User = Depends(require_vendor),
):
    """Only accessible with a vendor token."""
    return current_user


@router.get("/test/staff-only", response_model=UserResponse)
async def test_staff_only(
    current_user: User = Depends(require_vendor_or_admin),
):
    """Accessible with either vendor or admin token."""
    return current_user
