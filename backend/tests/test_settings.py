"""Tests for restaurant settings."""

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401
from app.api.dependencies import get_firebase_claims
from app.database.base import Base
from app.database.session import get_db
from app.main import app as fastapi_app
from app.models.user import User
from app.utils.enums import UserRole


@pytest.fixture()
def database_session() -> Generator[Session, None, None]:
    """Create an isolated database."""

    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    testing_session_local = sessionmaker(
        bind=engine,
        class_=Session,
        autoflush=False,
        autocommit=False,
        expire_on_commit=False,
    )

    Base.metadata.create_all(bind=engine)

    database = testing_session_local()

    try:
        yield database
    finally:
        database.close()
        Base.metadata.drop_all(bind=engine)


def build_client(
    database_session: Session,
    role: UserRole,
) -> TestClient:
    """Create a test client for a selected role."""

    firebase_uid = f"settings-{role.value.lower()}"

    user = User(
        firebase_uid=firebase_uid,
        full_name=f"{role.value.title()} User",
        email=f"{role.value.lower()}@example.com",
        role=role,
        is_active=True,
    )

    database_session.add(user)
    database_session.commit()

    def override_get_db():
        yield database_session

    def override_firebase_claims():
        return {
            "uid": firebase_uid,
            "sub": firebase_uid,
            "email": user.email,
        }

    fastapi_app.dependency_overrides[get_db] = override_get_db
    fastapi_app.dependency_overrides[
        get_firebase_claims
    ] = override_firebase_claims

    return TestClient(fastapi_app)


def test_admin_can_read_default_settings(
    database_session: Session,
) -> None:
    """Admin can load automatically created settings."""

    with build_client(
        database_session,
        UserRole.ADMIN,
    ) as client:
        response = client.get("/api/v1/settings")

    fastapi_app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["data"]["currency"] == "INR"
    assert (
        response.json()["data"]["restaurant_name"]
        == "LazyBites Restaurant"
    )


def test_admin_can_update_settings(
    database_session: Session,
) -> None:
    """Admin can edit restaurant information."""

    with build_client(
        database_session,
        UserRole.ADMIN,
    ) as client:
        response = client.put(
            "/api/v1/settings",
            json={
                "restaurant_name": "LazyBites River Restaurant",
                "address": "Jorhat, Assam",
                "phone": "9876543210",
                "email": "hello@lazybites.example",
                "gstin": "18ABCDE1234F1Z5",
                "default_gst_percentage": "5.00",
                "currency": "INR",
                "invoice_prefix": "LB",
                "receipt_footer": "Thank you for visiting.",
                "timezone": "Asia/Kolkata",
            },
        )

    fastapi_app.dependency_overrides.clear()

    assert response.status_code == 200
    assert (
        response.json()["data"]["restaurant_name"]
        == "LazyBites River Restaurant"
    )
    assert response.json()["data"]["invoice_prefix"] == "LB"


def test_staff_cannot_update_settings(
    database_session: Session,
) -> None:
    """Staff can view but cannot edit settings."""

    with build_client(
        database_session,
        UserRole.STAFF,
    ) as client:
        response = client.put(
            "/api/v1/settings",
            json={
                "restaurant_name": "Changed Name",
                "address": "Jorhat, Assam",
                "phone": "9876543210",
                "email": None,
                "gstin": None,
                "default_gst_percentage": "5.00",
                "currency": "INR",
                "invoice_prefix": "INV",
                "receipt_footer": None,
                "timezone": "Asia/Kolkata",
            },
        )

    fastapi_app.dependency_overrides.clear()

    assert response.status_code == 403