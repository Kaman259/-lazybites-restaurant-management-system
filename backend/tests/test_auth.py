"""Tests for Firebase authentication and local customer accounts."""

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


TEST_FIREBASE_CLAIMS = {
    "uid": "firebase-test-customer-001",
    "sub": "firebase-test-customer-001",
    "email": "customer@example.com",
    "email_verified": False,
}


@pytest.fixture()
def database_session() -> Generator[Session, None, None]:
    """Create an isolated in-memory database."""

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


@pytest.fixture()
def client(
    database_session: Session,
) -> Generator[TestClient, None, None]:
    """Create a client with database and Firebase overrides."""

    def override_get_db():
        yield database_session

    def override_firebase_claims():
        return TEST_FIREBASE_CLAIMS

    fastapi_app.dependency_overrides[get_db] = override_get_db
    fastapi_app.dependency_overrides[
        get_firebase_claims
    ] = override_firebase_claims

    with TestClient(fastapi_app) as test_client:
        yield test_client

    fastapi_app.dependency_overrides.clear()


def test_register_customer_creates_user_and_profile(
    client: TestClient,
) -> None:
    """Customer registration creates both local records."""

    response = client.post(
        "/api/v1/auth/register-customer",
        json={
            "full_name": "Test Customer",
            "phone": "9876543210",
            "address": "Jorhat, Assam",
        },
    )

    assert response.status_code == 201

    response_body = response.json()

    assert response_body["success"] is True
    assert response_body["data"]["user"]["role"] == "CUSTOMER"
    assert (
        response_body["data"]["user"]["email"]
        == "customer@example.com"
    )
    assert (
        response_body["data"]["customer"]["phone"]
        == "9876543210"
    )


def test_registering_same_customer_is_idempotent(
    client: TestClient,
) -> None:
    """Repeating registration returns the existing customer."""

    payload = {
        "full_name": "Test Customer",
        "phone": "9876543210",
        "address": "Jorhat, Assam",
    }

    first_response = client.post(
        "/api/v1/auth/register-customer",
        json=payload,
    )

    second_response = client.post(
        "/api/v1/auth/register-customer",
        json=payload,
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 201

    first_customer_id = first_response.json()["data"]["customer"]["id"]
    second_customer_id = second_response.json()["data"]["customer"]["id"]

    assert first_customer_id == second_customer_id


def test_current_account_requires_registered_user(
    client: TestClient,
) -> None:
    """A Firebase identity without a local account is rejected."""

    response = client.get("/api/v1/auth/me")

    assert response.status_code == 404
    assert response.json()["success"] is False


def test_current_account_returns_registered_customer(
    client: TestClient,
) -> None:
    """A registered Firebase user can retrieve their account."""

    client.post(
        "/api/v1/auth/register-customer",
        json={
            "full_name": "Test Customer",
            "phone": "9876543210",
        },
    )

    response = client.get("/api/v1/auth/me")

    assert response.status_code == 200
    assert response.json()["data"]["user"]["role"] == "CUSTOMER"
    assert response.json()["data"]["customer"] is not None


def test_customer_cannot_access_admin_endpoint(
    client: TestClient,
) -> None:
    """Customer role cannot use Admin-only routes."""

    client.post(
        "/api/v1/auth/register-customer",
        json={
            "full_name": "Test Customer",
            "phone": "9876543210",
        },
    )

    response = client.get("/api/v1/auth/admin-check")

    assert response.status_code == 403
    assert response.json()["success"] is False