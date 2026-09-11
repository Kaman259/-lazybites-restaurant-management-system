"""Firebase Admin initialisation and ID token verification."""

import json
from functools import lru_cache
from typing import Any

import firebase_admin
from firebase_admin import (
    auth,
    credentials,
)
from firebase_admin.auth import (
    ExpiredIdTokenError,
    InvalidIdTokenError,
    RevokedIdTokenError,
)

from app.core.config import settings
from app.core.exceptions import (
    AppException,
)


def build_firebase_credentials():
    """
    Load Firebase Admin credentials.

    Production can provide credentials through an
    environment variable. Local development can
    continue using the service-account JSON file.
    """

    credentials_json = (
        settings.firebase_credentials_json
    )

    if (
        credentials_json
        and credentials_json.strip()
    ):
        try:
            credentials_data = json.loads(
                credentials_json
            )

            return credentials.Certificate(
                credentials_data
            )

        except (
            json.JSONDecodeError,
            ValueError,
            TypeError,
        ) as exception:
            raise AppException(
                message=(
                    "Firebase Admin credentials "
                    "are invalid."
                ),
                status_code=500,
            ) from exception

    credentials_path = (
        settings.firebase_credentials_file
    )

    if not credentials_path.exists():
        raise AppException(
            message=(
                "Firebase Admin credentials "
                "were not configured."
            ),
            status_code=500,
        )

    try:
        return credentials.Certificate(
            str(credentials_path)
        )

    except (
        ValueError,
        OSError,
    ) as exception:
        raise AppException(
            message=(
                "Firebase Admin could not "
                "load its credentials."
            ),
            status_code=500,
        ) from exception


@lru_cache
def get_firebase_app() -> (
    firebase_admin.App
):
    """Initialise the Firebase Admin application."""

    try:
        return firebase_admin.get_app()

    except ValueError:
        pass

    try:
        certificate = (
            build_firebase_credentials()
        )

        return firebase_admin.initialize_app(
            certificate
        )

    except AppException:
        raise

    except (
        ValueError,
        OSError,
    ) as exception:
        raise AppException(
            message=(
                "Firebase Admin could not "
                "be initialised."
            ),
            status_code=500,
        ) from exception


def verify_firebase_id_token(
    id_token: str,
) -> dict[str, Any]:
    """Verify Firebase ID token and return claims."""

    if (
        not id_token
        or not id_token.strip()
    ):
        raise AppException(
            message=(
                "Authentication token "
                "is required."
            ),
            status_code=401,
        )

    try:
        decoded_token = (
            auth.verify_id_token(
                id_token.strip(),
                app=get_firebase_app(),
                check_revoked=(
                    settings
                    .firebase_check_revoked
                ),
            )
        )

    except ExpiredIdTokenError as exception:
        raise AppException(
            message=(
                "Your login session has expired. "
                "Please sign in again."
            ),
            status_code=401,
        ) from exception

    except RevokedIdTokenError as exception:
        raise AppException(
            message=(
                "Your login session "
                "has been revoked."
            ),
            status_code=401,
        ) from exception

    except InvalidIdTokenError as exception:
        raise AppException(
            message=(
                "The authentication token "
                "is invalid."
            ),
            status_code=401,
        ) from exception

    except ValueError as exception:
        raise AppException(
            message=(
                "The authentication token "
                "is invalid."
            ),
            status_code=401,
        ) from exception

    firebase_uid = (
        decoded_token.get("uid")
        or decoded_token.get("sub")
    )

    email = decoded_token.get(
        "email"
    )

    if not firebase_uid:
        raise AppException(
            message=(
                "Firebase user identifier "
                "is missing."
            ),
            status_code=401,
        )

    if not email:
        raise AppException(
            message=(
                "An email address is required "
                "for this account."
            ),
            status_code=401,
        )

    return decoded_token