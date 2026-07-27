"""Role-based permission helpers."""

from collections.abc import Callable
from typing import Annotated

from fastapi import Depends

from app.api.dependencies import get_current_user
from app.core.exceptions import AppException
from app.models.user import User
from app.utils.enums import UserRole


CurrentUser = Annotated[User, Depends(get_current_user)]


def require_roles(
    *allowed_roles: UserRole,
) -> Callable[[CurrentUser], User]:
    """Create a dependency that allows selected user roles."""

    def role_checker(current_user: CurrentUser) -> User:
        if current_user.role not in allowed_roles:
            raise AppException(
                message="You do not have permission to perform this action.",
                status_code=403,
            )

        return current_user

    return role_checker


require_admin = require_roles(UserRole.ADMIN)

require_staff_or_admin = require_roles(
    UserRole.ADMIN,
    UserRole.STAFF,
)

require_customer = require_roles(UserRole.CUSTOMER)