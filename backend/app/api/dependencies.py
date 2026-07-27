"""Common FastAPI dependencies."""

from typing import Annotated, Any

from fastapi import Depends, Header
from sqlalchemy.orm import Session

from app.auth.firebase import verify_firebase_id_token
from app.core.exceptions import AppException
from app.database.session import get_db
from app.models.user import User
from app.services.auth_service import get_user_by_firebase_uid


DatabaseSession = Annotated[Session, Depends(get_db)]


def extract_bearer_token(
    authorization: Annotated[str | None, Header()] = None,
) -> str:
    """Extract a bearer token from the Authorization header."""

    if not authorization:
        raise AppException(
            message="Authentication is required.",
            status_code=401,
        )

    scheme, separator, token = authorization.partition(" ")

    if (
        separator != " "
        or scheme.lower() != "bearer"
        or not token.strip()
    ):
        raise AppException(
            message="Use a valid Bearer authentication token.",
            status_code=401,
        )

    return token.strip()


def get_firebase_claims(
    id_token: Annotated[str, Depends(extract_bearer_token)],
) -> dict[str, Any]:
    """Verify the request token and return Firebase claims."""

    return verify_firebase_id_token(id_token)


FirebaseClaims = Annotated[
    dict[str, Any],
    Depends(get_firebase_claims),
]


def get_current_user(
    database: DatabaseSession,
    firebase_claims: FirebaseClaims,
) -> User:
    """Return the active local user matching Firebase claims."""

    firebase_uid = str(
        firebase_claims.get("uid") or firebase_claims.get("sub")
    )

    user = get_user_by_firebase_uid(
        database,
        firebase_uid,
    )

    if user is None:
        raise AppException(
            message=(
                "This Firebase account has not been registered "
                "inside the restaurant system."
            ),
            status_code=404,
        )

    if not user.is_active:
        raise AppException(
            message="This account has been deactivated.",
            status_code=403,
        )

    return user


CurrentUser = Annotated[User, Depends(get_current_user)]