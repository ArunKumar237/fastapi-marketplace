from typing import Union

from fastapi import Depends

from app.dependencies.auth import get_current_user
from app.exceptions import ForbiddenException
from app.models.user import User, UserRole


def require_role(role: Union[str, list[str]]):
    """
    Factory function that returns a FastAPI dependency.

    Usage:
        @router.get("/admin-only")
        async def admin_route(user: User = Depends(require_role("admin"))):
            ...

        @router.get("/staff")
        async def staff_route(user: User = Depends(require_role(["vendor", "admin"]))):
            ...
    """

    # Normalise to a list so we handle single string and list uniformly
    if isinstance(role, str):
        allowed_roles = [UserRole(role)]
    else:
        allowed_roles = [UserRole(r) for r in role]

    async def _role_checker(
        current_user: User = Depends(get_current_user),
    ) -> User:
        if current_user.role not in allowed_roles:
            raise ForbiddenException(
                detail=(
                    f"Role '{current_user.role.value}' is not permitted "
                    f"to access this resource. Required: "
                    f"{[r.value for r in allowed_roles]}"
                ),
                error_code="INSUFFICIENT_PERMISSIONS",
            )
        return current_user

    return _role_checker


# -------------------------------------------------
# Convenience shortcuts — use directly as dependencies
# -------------------------------------------------
require_admin = require_role("admin")
require_vendor = require_role("vendor")
require_customer = require_role("customer")
require_vendor_or_admin = require_role(["vendor", "admin"])
