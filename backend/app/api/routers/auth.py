"""Authentication and account synchronisation endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.api.dependencies import (
    CurrentUser,
    DatabaseSession,
    FirebaseClaims,
)
from app.auth.permissions import (
    require_admin,
    require_staff_or_admin,
)
from app.core.responses import success_response
from app.models.user import User
from app.schemas.auth import (
    AccountProfileUpdate,
    AuthSessionResponse,
    AuthUserResponse,
    CustomerProfileSummary,
    CustomerRegistrationRequest,
)
from app.services.auth_service import (
    create_auth_session,
    get_customer_for_user,
    register_customer_account,
    update_account_profile,
)


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)

AdminUser = Annotated[
    User,
    Depends(require_admin),
]

StaffUser = Annotated[
    User,
    Depends(require_staff_or_admin),
]


def build_session_response(
    user: User,
    customer,
) -> dict:
    """Build the standard authenticated account response."""

    response_data = AuthSessionResponse(
        user=AuthUserResponse.model_validate(user),
        customer=(
            CustomerProfileSummary.model_validate(
                customer
            )
            if customer is not None
            else None
        ),
    )

    return response_data.model_dump(
        mode="json",
    )


@router.post(
    "/register-customer",
    status_code=status.HTTP_201_CREATED,
    summary="Register a Firebase customer locally",
)
def register_customer(
    registration_data: CustomerRegistrationRequest,
    database: DatabaseSession,
    firebase_claims: FirebaseClaims,
):
    """Create the local customer account after Firebase registration."""

    user, customer = register_customer_account(
        database=database,
        firebase_claims=firebase_claims,
        registration_data=registration_data,
    )

    return success_response(
        message=(
            "Customer account created successfully."
        ),
        data=build_session_response(
            user,
            customer,
        ),
        status_code=status.HTTP_201_CREATED,
    )


@router.post(
    "/session",
    summary="Create or refresh an application session",
)
def create_session(
    current_user: CurrentUser,
    database: DatabaseSession,
):
    """Update the user's last-login time."""

    user, customer = create_auth_session(
        database=database,
        user=current_user,
    )

    return success_response(
        message=(
            "Login session created successfully."
        ),
        data=build_session_response(
            user,
            customer,
        ),
    )


@router.get(
    "/me",
    summary="Get the authenticated account",
)
def read_current_account(
    current_user: CurrentUser,
    database: DatabaseSession,
):
    """Return the currently authenticated local account."""

    customer = get_customer_for_user(
        database,
        current_user.id,
    )

    return success_response(
        message=(
            "Authenticated account retrieved "
            "successfully."
        ),
        data=build_session_response(
            current_user,
            customer,
        ),
    )


@router.patch(
    "/me",
    summary="Update the authenticated account",
)
def change_current_account(
    profile_data: AccountProfileUpdate,
    current_user: CurrentUser,
    database: DatabaseSession,
):
    """Update editable profile fields for the current user."""

    user, customer = update_account_profile(
        database=database,
        user=current_user,
        profile_data=profile_data,
    )

    return success_response(
        message="Profile updated successfully.",
        data=build_session_response(
            user,
            customer,
        ),
    )


@router.get(
    "/admin-check",
    summary="Verify Admin access",
)
def admin_access_check(
    current_user: AdminUser,
):
    """Return success when the current user is an Admin."""

    return success_response(
        message="Admin permission confirmed.",
        data={
            "user_id": current_user.id,
        },
    )


@router.get(
    "/staff-check",
    summary="Verify Staff or Admin access",
)
def staff_access_check(
    current_user: StaffUser,
):
    """Return success for Staff and Admin users."""

    return success_response(
        message="Staff permission confirmed.",
        data={
            "user_id": current_user.id,
        },
    )