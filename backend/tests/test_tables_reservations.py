"""Tests for dining tables and customer reservations."""

from collections.abc import Generator
from datetime import datetime, timedelta, timezone

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
from app.models.customer import Customer
from app.models.user import User
from app.utils.enums import UserRole


@pytest.fixture()
def database_session() -> Generator[Session, None, None]:
    """Create an isolated SQLite database."""

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
    """Create a test client for a selected application role."""

    firebase_uid = f"table-test-{role.value.lower()}"

    user = User(
        firebase_uid=firebase_uid,
        full_name=f"{role.value.title()} User",
        email=f"{role.value.lower()}-table@example.com",
        role=role,
        is_active=True,
    )

    database_session.add(user)
    database_session.commit()
    database_session.refresh(user)

    if role == UserRole.CUSTOMER:
        customer = Customer(
            user_id=user.id,
            full_name=user.full_name,
            email=user.email,
            phone="9876543210",
            is_active=True,
        )
        database_session.add(customer)
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


def clear_overrides() -> None:
    """Clear FastAPI dependency overrides."""

    fastapi_app.dependency_overrides.clear()


def test_admin_can_create_and_list_table(
    database_session: Session,
) -> None:
    """Admin can create and retrieve a dining table."""

    with build_client(
        database_session,
        UserRole.ADMIN,
    ) as client:
        create_response = client.post(
            "/api/v1/tables",
            json={
                "table_number": "T-01",
                "capacity": 4,
                "area": "Main Hall",
                "description": "Near the window",
                "is_active": True,
            },
        )

        list_response = client.get("/api/v1/tables")

    clear_overrides()

    assert create_response.status_code == 201
    assert create_response.json()["data"]["table_number"] == "T-01"
    assert list_response.status_code == 200
    assert len(list_response.json()["data"]) == 1


def test_staff_cannot_create_table(
    database_session: Session,
) -> None:
    """Staff can view tables but cannot create them."""

    with build_client(
        database_session,
        UserRole.STAFF,
    ) as client:
        response = client.post(
            "/api/v1/tables",
            json={
                "table_number": "T-02",
                "capacity": 2,
                "area": "Patio",
                "description": None,
                "is_active": True,
            },
        )

    clear_overrides()

    assert response.status_code == 403


def test_customer_can_find_and_reserve_table(
    database_session: Session,
) -> None:
    """Customer can search for and reserve an available table."""

    with build_client(
        database_session,
        UserRole.ADMIN,
    ) as admin_client:
        table_response = admin_client.post(
            "/api/v1/tables",
            json={
                "table_number": "T-03",
                "capacity": 4,
                "area": "Main Hall",
                "description": None,
                "is_active": True,
            },
        )

    clear_overrides()

    table_id = table_response.json()["data"]["id"]
    start_time = datetime.now(timezone.utc) + timedelta(days=2)
    end_time = start_time + timedelta(hours=2)

    with build_client(
        database_session,
        UserRole.CUSTOMER,
    ) as customer_client:
        availability_response = customer_client.post(
            "/api/v1/reservations/availability",
            json={
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "guest_count": 3,
            },
        )

        reservation_response = customer_client.post(
            "/api/v1/reservations",
            json={
                "table_id": table_id,
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "guest_count": 3,
                "notes": "Birthday dinner",
            },
        )

    clear_overrides()

    assert availability_response.status_code == 200
    assert len(availability_response.json()["data"]) == 1
    assert reservation_response.status_code == 201
    assert (
        reservation_response.json()["data"]["status"]
        == "PENDING"
    )


def test_overlapping_reservation_is_blocked(
    database_session: Session,
) -> None:
    """Two active reservations cannot overlap on one table."""

    with build_client(
        database_session,
        UserRole.ADMIN,
    ) as admin_client:
        table_response = admin_client.post(
            "/api/v1/tables",
            json={
                "table_number": "T-04",
                "capacity": 6,
                "area": "River Side",
                "description": None,
                "is_active": True,
            },
        )

    clear_overrides()

    table_id = table_response.json()["data"]["id"]
    start_time = datetime.now(timezone.utc) + timedelta(days=3)
    end_time = start_time + timedelta(hours=2)

    with build_client(
        database_session,
        UserRole.CUSTOMER,
    ) as customer_client:
        first_response = customer_client.post(
            "/api/v1/reservations",
            json={
                "table_id": table_id,
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "guest_count": 4,
                "notes": None,
            },
        )

        second_response = customer_client.post(
            "/api/v1/reservations",
            json={
                "table_id": table_id,
                "start_time": (
                    start_time + timedelta(minutes=30)
                ).isoformat(),
                "end_time": (
                    end_time + timedelta(minutes=30)
                ).isoformat(),
                "guest_count": 2,
                "notes": None,
            },
        )

    clear_overrides()

    assert first_response.status_code == 201
    assert second_response.status_code == 409


def test_customer_can_cancel_own_reservation(
    database_session: Session,
) -> None:
    """Customer can cancel their future pending reservation."""

    with build_client(
        database_session,
        UserRole.ADMIN,
    ) as admin_client:
        table_response = admin_client.post(
            "/api/v1/tables",
            json={
                "table_number": "T-05",
                "capacity": 2,
                "area": "Balcony",
                "description": None,
                "is_active": True,
            },
        )

    clear_overrides()

    start_time = datetime.now(timezone.utc) + timedelta(days=4)
    end_time = start_time + timedelta(hours=1)

    with build_client(
        database_session,
        UserRole.CUSTOMER,
    ) as customer_client:
        reservation_response = customer_client.post(
            "/api/v1/reservations",
            json={
                "table_id": table_response.json()["data"]["id"],
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "guest_count": 2,
                "notes": None,
            },
        )

        reservation_id = reservation_response.json()["data"]["id"]

        cancel_response = customer_client.patch(
            f"/api/v1/reservations/{reservation_id}/cancel",
            json={
                "cancellation_reason": "Plans changed",
            },
        )

    clear_overrides()

    assert cancel_response.status_code == 200
    assert (
        cancel_response.json()["data"]["status"]
        == "CANCELLED"
    )