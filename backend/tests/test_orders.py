"""Tests for restaurant order management."""

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
    """Create an isolated SQLite database."""

    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={
            "check_same_thread": False,
        },
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

    firebase_uid = f"order-test-{role.value.lower()}"

    user = User(
        firebase_uid=firebase_uid,
        full_name=f"{role.value.title()} User",
        email=f"{role.value.lower()}-order@example.com",
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

    fastapi_app.dependency_overrides[
        get_db
    ] = override_get_db

    fastapi_app.dependency_overrides[
        get_firebase_claims
    ] = override_firebase_claims

    return TestClient(fastapi_app)


def clear_overrides() -> None:
    """Clear FastAPI dependency overrides."""

    fastapi_app.dependency_overrides.clear()


def create_category_and_item(
    client: TestClient,
    item_name: str = "Veg Fried Rice",
    price: str = "180.00",
) -> int:
    """Create a category and menu item through the API."""

    category_response = client.post(
        "/api/v1/menu/categories",
        json={
            "name": f"Order Category {item_name}",
            "description": None,
            "display_order": 1,
            "is_active": True,
        },
    )

    category_id = category_response.json()["data"]["id"]

    item_response = client.post(
        "/api/v1/menu/items",
        json={
            "category_id": category_id,
            "name": item_name,
            "description": None,
            "price": price,
            "food_type": "VEG",
            "is_available": True,
            "is_active": True,
        },
    )

    return item_response.json()["data"]["id"]


def create_table(client: TestClient) -> int:
    """Create one active dining table."""

    response = client.post(
        "/api/v1/tables",
        json={
            "table_number": "ORDER-T-01",
            "capacity": 4,
            "area": "Main Hall",
            "description": None,
            "is_active": True,
        },
    )

    return response.json()["data"]["id"]


def test_staff_can_create_takeaway_order(
    database_session: Session,
) -> None:
    """Staff can create a takeaway order with calculated totals."""

    with build_client(
        database_session,
        UserRole.ADMIN,
    ) as admin_client:
        item_id = create_category_and_item(
            admin_client,
            price="180.00",
        )

    clear_overrides()

    with build_client(
        database_session,
        UserRole.STAFF,
    ) as staff_client:
        response = staff_client.post(
            "/api/v1/orders",
            json={
                "customer_id": None,
                "table_id": None,
                "reservation_id": None,
                "order_type": "TAKEAWAY",
                "special_instructions": None,
                "delivery_address": None,
                "items": [
                    {
                        "menu_item_id": item_id,
                        "quantity": 2,
                        "special_instruction": (
                            "Less spicy"
                        ),
                    }
                ],
            },
        )

    clear_overrides()

    assert response.status_code == 201
    assert response.json()["data"]["status"] == "PENDING"
    assert response.json()["data"]["subtotal"] == "360.00"
    assert (
        response.json()["data"]["items"][0]["line_total"]
        == "360.00"
    )


def test_dine_in_order_requires_table(
    database_session: Session,
) -> None:
    """A dine-in order cannot be created without a table."""

    with build_client(
        database_session,
        UserRole.ADMIN,
    ) as client:
        item_id = create_category_and_item(client)

        response = client.post(
            "/api/v1/orders",
            json={
                "customer_id": None,
                "table_id": None,
                "reservation_id": None,
                "order_type": "DINE_IN",
                "special_instructions": None,
                "delivery_address": None,
                "items": [
                    {
                        "menu_item_id": item_id,
                        "quantity": 1,
                        "special_instruction": None,
                    }
                ],
            },
        )

    clear_overrides()

    assert response.status_code == 400


def test_delivery_order_requires_address(
    database_session: Session,
) -> None:
    """A delivery order must include a delivery address."""

    with build_client(
        database_session,
        UserRole.ADMIN,
    ) as client:
        item_id = create_category_and_item(client)

        response = client.post(
            "/api/v1/orders",
            json={
                "customer_id": None,
                "table_id": None,
                "reservation_id": None,
                "order_type": "DELIVERY",
                "special_instructions": None,
                "delivery_address": None,
                "items": [
                    {
                        "menu_item_id": item_id,
                        "quantity": 1,
                        "special_instruction": None,
                    }
                ],
            },
        )

    clear_overrides()

    assert response.status_code == 400


def test_order_status_follows_allowed_sequence(
    database_session: Session,
) -> None:
    """An order can move through its supported workflow."""

    with build_client(
        database_session,
        UserRole.ADMIN,
    ) as client:
        item_id = create_category_and_item(client)
        table_id = create_table(client)

        create_response = client.post(
            "/api/v1/orders",
            json={
                "customer_id": None,
                "table_id": table_id,
                "reservation_id": None,
                "order_type": "DINE_IN",
                "special_instructions": None,
                "delivery_address": None,
                "items": [
                    {
                        "menu_item_id": item_id,
                        "quantity": 1,
                        "special_instruction": None,
                    }
                ],
            },
        )

        order_id = create_response.json()["data"]["id"]

        preparing_response = client.patch(
            f"/api/v1/orders/{order_id}/status",
            json={
                "status": "PREPARING",
                "cancellation_reason": None,
            },
        )

        ready_response = client.patch(
            f"/api/v1/orders/{order_id}/status",
            json={
                "status": "READY",
                "cancellation_reason": None,
            },
        )

        served_response = client.patch(
            f"/api/v1/orders/{order_id}/status",
            json={
                "status": "SERVED",
                "cancellation_reason": None,
            },
        )

        completed_response = client.patch(
            f"/api/v1/orders/{order_id}/status",
            json={
                "status": "COMPLETED",
                "cancellation_reason": None,
            },
        )

    clear_overrides()

    assert preparing_response.status_code == 200
    assert ready_response.status_code == 200
    assert served_response.status_code == 200
    assert completed_response.status_code == 200

    assert (
        completed_response.json()["data"]["status"]
        == "COMPLETED"
    )


def test_invalid_order_status_jump_is_blocked(
    database_session: Session,
) -> None:
    """An order cannot jump directly from pending to completed."""

    with build_client(
        database_session,
        UserRole.ADMIN,
    ) as client:
        item_id = create_category_and_item(client)

        create_response = client.post(
            "/api/v1/orders",
            json={
                "customer_id": None,
                "table_id": None,
                "reservation_id": None,
                "order_type": "TAKEAWAY",
                "special_instructions": None,
                "delivery_address": None,
                "items": [
                    {
                        "menu_item_id": item_id,
                        "quantity": 1,
                        "special_instruction": None,
                    }
                ],
            },
        )

        order_id = create_response.json()["data"]["id"]

        response = client.patch(
            f"/api/v1/orders/{order_id}/status",
            json={
                "status": "COMPLETED",
                "cancellation_reason": None,
            },
        )

    clear_overrides()

    assert response.status_code == 409