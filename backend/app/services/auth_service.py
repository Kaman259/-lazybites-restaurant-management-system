"""Authentication and local account synchronisation services."""

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import AppException
from app.models.customer import Customer
from app.models.user import User
from app.schemas.auth import CustomerRegistrationRequest
from app.utils.enums import UserRole


def normalise_email(email: str) -> str:
    """Return a lowercase email address without outer whitespace."""

    return email.strip().lower()


def get_user_by_firebase_uid(
    database: Session,
    firebase_uid: str,
) -> User | None:
    """Find a local user by Firebase UID."""

    statement = select(User).where(
        User.firebase_uid == firebase_uid
    )

    return database.scalar(statement)


def get_user_by_email(
    database: Session,
    email: str,
) -> User | None:
    """Find a local user by normalised email."""

    statement = select(User).where(
        User.email == normalise_email(email)
    )

    return database.scalar(statement)


def get_customer_for_user(
    database: Session,
    user_id: int,
) -> Customer | None:
    """Find the customer profile linked to a user."""

    statement = select(Customer).where(
        Customer.user_id == user_id
    )

    return database.scalar(statement)


def register_customer_account(
    database: Session,
    firebase_claims: dict[str, Any],
    registration_data: CustomerRegistrationRequest,
) -> tuple[User, Customer]:
    """Create a customer user and linked customer profile."""

    firebase_uid = str(
        firebase_claims.get("uid") or firebase_claims.get("sub")
    )
    email = normalise_email(str(firebase_claims.get("email", "")))

    existing_uid_user = get_user_by_firebase_uid(
        database,
        firebase_uid,
    )

    if existing_uid_user is not None:
        existing_customer = get_customer_for_user(
            database,
            existing_uid_user.id,
        )

        if (
            existing_uid_user.role == UserRole.CUSTOMER
            and existing_customer is not None
        ):
            return existing_uid_user, existing_customer

        raise AppException(
            message="This Firebase account is already registered.",
            status_code=409,
        )

    existing_email_user = get_user_by_email(database, email)

    if existing_email_user is not None:
        raise AppException(
            message="An account with this email already exists.",
            status_code=409,
        )

    user = User(
        firebase_uid=firebase_uid,
        full_name=registration_data.full_name,
        email=email,
        role=UserRole.CUSTOMER,
        is_active=True,
        last_login_at=datetime.now(timezone.utc),
    )

    customer = Customer(
        user=user,
        full_name=registration_data.full_name,
        phone=registration_data.phone,
        email=email,
        address=registration_data.address,
        is_active=True,
    )

    database.add(user)
    database.add(customer)

    try:
        database.commit()
    except IntegrityError as exception:
        database.rollback()

        raise AppException(
            message="The customer account could not be created.",
            status_code=409,
        ) from exception

    database.refresh(user)
    database.refresh(customer)

    return user, customer


def create_auth_session(
    database: Session,
    user: User,
) -> tuple[User, Customer | None]:
    """Update last-login time and return the account session."""

    if not user.is_active:
        raise AppException(
            message="This account has been deactivated.",
            status_code=403,
        )

    user.last_login_at = datetime.now(timezone.utc)
    database.add(user)
    database.commit()
    database.refresh(user)

    customer = None

    if user.role == UserRole.CUSTOMER:
        customer = get_customer_for_user(database, user.id)

        if customer is None:
            raise AppException(
                message="The customer profile is missing.",
                status_code=409,
            )

        if not customer.is_active:
            raise AppException(
                message="This customer profile has been deactivated.",
                status_code=403,
            )

    return user, customer