"""Tests for menu category and menu-item management."""

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
    """Create a test client for one role."""

    firebase_uid = f"menu-test-{role.value.lower()}"

    user = User(
        firebase_uid=firebase_uid,
        full_name=f"{role.value.title()} User",
        email=f"{role.value.lower()}-menu@example.com",
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


def clear_overrides() -> None:
    """Clear FastAPI test overrides."""

    fastapi_app.dependency_overrides.clear()


def test_admin_can_create_category_and_item(
    database_session: Session,
) -> None:
    """Admin can create a category and menu item."""

    with build_client(
        database_session,
        UserRole.ADMIN,
    ) as client:
        category_response = client.post(
            "/api/v1/menu/categories",
            json={
                "name": "Main Course",
                "description": "Restaurant main dishes",
                "display_order": 1,
                "is_active": True,
            },
        )

        category_id = category_response.json()["data"]["id"]

        item_response = client.post(
            "/api/v1/menu/items",
            json={
                "category_id": category_id,
                "name": "Paneer Butter Masala",
                "description": "Paneer in tomato gravy",
                "price": "220.00",
                "food_type": "VEG",
                "is_available": True,
                "is_active": True,
            },
        )

    clear_overrides()

    assert category_response.status_code == 201
    assert item_response.status_code == 201
    assert (
        item_response.json()["data"]["name"]
        == "Paneer Butter Masala"
    )
    assert item_response.json()["data"]["food_type"] == "VEG"


def test_staff_can_read_but_cannot_create_menu_item(
    database_session: Session,
) -> None:
    """Staff can view menu records but cannot create them."""

    with build_client(
        database_session,
        UserRole.STAFF,
    ) as client:
        list_response = client.get("/api/v1/menu/items")

        create_response = client.post(
            "/api/v1/menu/items",
            json={
                "category_id": 1,
                "name": "Blocked Item",
                "description": None,
                "price": "100.00",
                "food_type": "VEG",
                "is_available": True,
                "is_active": True,
            },
        )

    clear_overrides()

    assert list_response.status_code == 200
    assert create_response.status_code == 403


def test_duplicate_item_name_in_category_is_blocked(
    database_session: Session,
) -> None:
    """Item names must be unique inside the same category."""

    with build_client(
        database_session,
        UserRole.ADMIN,
    ) as client:
        category_response = client.post(
            "/api/v1/menu/categories",
            json={
                "name": "Starters",
                "description": None,
                "display_order": 1,
                "is_active": True,
            },
        )

        category_id = category_response.json()["data"]["id"]

        payload = {
            "category_id": category_id,
            "name": "Veg Pakora",
            "description": None,
            "price": "120.00",
            "food_type": "VEG",
            "is_available": True,
            "is_active": True,
        }

        first_response = client.post(
            "/api/v1/menu/items",
            json=payload,
        )

        second_response = client.post(
            "/api/v1/menu/items",
            json=payload,
        )

    clear_overrides()

    assert first_response.status_code == 201
    assert second_response.status_code == 409


def test_staff_can_change_item_availability(
    database_session: Session,
) -> None:
    """Staff can mark a menu item unavailable."""

    with build_client(
        database_session,
        UserRole.ADMIN,
    ) as admin_client:
        category_response = admin_client.post(
            "/api/v1/menu/categories",
            json={
                "name": "Drinks",
                "description": None,
                "display_order": 1,
                "is_active": True,
            },
        )

        item_response = admin_client.post(
            "/api/v1/menu/items",
            json={
                "category_id": (
                    category_response.json()["data"]["id"]
                ),
                "name": "Fresh Lime",
                "description": None,
                "price": "80.00",
                "food_type": "VEG",
                "is_available": True,
                "is_active": True,
            },
        )

    clear_overrides()

    item_id = item_response.json()["data"]["id"]

    with build_client(
        database_session,
        UserRole.STAFF,
    ) as staff_client:
        response = staff_client.patch(
            f"/api/v1/menu/items/{item_id}/availability",
            json={
                "is_available": False,
            },
        )

    clear_overrides()

    assert response.status_code == 200
    assert response.json()["data"]["is_available"] is False


def test_category_with_items_cannot_be_deleted(
    database_session: Session,
) -> None:
    """A populated category must be disabled instead of deleted."""

    with build_client(
        database_session,
        UserRole.ADMIN,
    ) as client:
        category_response = client.post(
            "/api/v1/menu/categories",
            json={
                "name": "Desserts",
                "description": None,
                "display_order": 1,
                "is_active": True,
            },
        )

        category_id = category_response.json()["data"]["id"]

        client.post(
            "/api/v1/menu/items",
            json={
                "category_id": category_id,
                "name": "Ice Cream",
                "description": None,
                "price": "90.00",
                "food_type": "VEG",
                "is_available": True,
                "is_active": True,
            },
        )

        delete_response = client.delete(
            f"/api/v1/menu/categories/{category_id}"
        )

    clear_overrides()

    assert delete_response.status_code == 409