import uuid

from app.models.user import User
from app.repositories.user import UserRepository
from app.schemas.user import UserCreate
from app.services.auth import (
    create_access_token,
    create_refresh_token,
    hash_password,
    verify_password,
)

# -------------------------
# Custom Exceptions
# -------------------------


class DuplicateEmailException(Exception):
    pass


class InvalidCredentialsException(Exception):
    pass


class InactiveUserException(Exception):
    pass


# =====================================================
# USER SERVICE
# =====================================================


class UserService:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    # -------------------------------------------------
    # REGISTER
    # -------------------------------------------------
    async def register(self, user_data: UserCreate) -> User:
        # Check if email already exists
        existing_user = await self.user_repo.get_by_email(user_data.email)
        if existing_user:
            raise DuplicateEmailException("Email already registered")

        # Hash password
        hashed_pw = hash_password(user_data.password)

        # Prepare DB payload
        new_user_data = {
            "email": user_data.email,
            "hashed_password": hashed_pw,
            "full_name": user_data.full_name,
            "role": user_data.role,  # optionally override to CUSTOMER
            "phone": user_data.phone,
        }

        # Save to DB
        user = await self.user_repo.create(new_user_data)

        return user

    # -------------------------------------------------
    # AUTHENTICATE (LOGIN)
    # -------------------------------------------------
    async def authenticate(self, email: str, password: str) -> dict:
        user = await self.user_repo.get_by_email(email)

        # Check user exists
        if not user:
            raise InvalidCredentialsException("Invalid email or password")

        # Check password
        if not verify_password(password, user.hashed_password):
            raise InvalidCredentialsException("Invalid email or password")

        # Check active
        if not user.is_active:
            raise InactiveUserException("Account is inactive")

        # Generate tokens
        access_token = create_access_token(user.id, user.role.value)
        refresh_token = create_refresh_token(user.id, user.role.value)

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
        }

    # -------------------------------------------------
    # GET PROFILE
    # -------------------------------------------------
    async def get_profile(self, user_id: uuid.UUID) -> User:
        user = await self.user_repo.get_by_id(user_id)

        if not user:
            raise InvalidCredentialsException("User not found")

        if not user.is_active:
            raise InactiveUserException("Account is inactive")

        return user
