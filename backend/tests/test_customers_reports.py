"""Tests for customers, dashboard, and reports."""

from collections.abc import Generator
from datetime import datetime, timezone
from decimal import Decimal

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
from app.models.invoice import Invoice
from app.models.menu_category import MenuCategory
from app.models.menu_item import MenuItem
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.user import User
from app.utils.enums import (
    DiscountType,
    FoodType,
    OrderStatus,
    OrderType,
    PaymentMethod,
    PaymentStatus,
    UserRole,
)


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
    database: Session,
    role: UserRole = UserRole.ADMIN,
) -> tuple[TestClient, User]:
    """Create an authenticated test client."""

    user = User(
        firebase_uid=f"customer-report-{role.value}",
        full_name=f"{role.value.title()} User",
        email=f"{role.value.lower()}-report@example.com",
        role=role,
        is_active=True,
    )

    database.add(user)
    database.commit()

    def override_get_db():
        yield database

    def override_firebase_claims():
        return {
            "uid": user.firebase_uid,
            "sub": user.firebase_uid,
            "email": user.email,
        }

    fastapi_app.dependency_overrides[
        get_db
    ] = override_get_db

    fastapi_app.dependency_overrides[
        get_firebase_claims
    ] = override_firebase_claims

    return TestClient(fastapi_app), user


def clear_overrides() -> None:
    """Clear FastAPI dependency overrides."""

    fastapi_app.dependency_overrides.clear()


def create_paid_order(
    database: Session,
    user: User,
    customer_id: int,
) -> None:
    """Create paid order data used by report tests."""

    category = MenuCategory(
        name="Report Category",
        description=None,
        display_order=1,
        is_active=True,
    )

    database.add(category)
    database.flush()

    menu_item = MenuItem(
        category_id=category.id,
        name="Report Meal",
        description=None,
        price=Decimal("200.00"),
        food_type=FoodType.VEG,
        image_path=None,
        is_available=True,
        is_active=True,
    )

    database.add(menu_item)
    database.flush()

    order = Order(
        order_number="LB-REPORT-ORDER-1",
        customer_id=customer_id,
        table_id=None,
        reservation_id=None,
        created_by_user_id=user.id,
        order_type=OrderType.TAKEAWAY,
        status=OrderStatus.COMPLETED,
        special_instructions=None,
        delivery_address=None,
        completed_at=datetime.now(
            timezone.utc
        ).replace(tzinfo=None),
    )

    database.add(order)
    database.flush()

    database.add(
        OrderItem(
            order_id=order.id,
            menu_item_id=menu_item.id,
            item_name=menu_item.name,
            unit_price=Decimal("200.00"),
            quantity=2,
            special_instruction=None,
            line_total=Decimal("400.00"),
        )
    )

    database.add(
        Invoice(
            order_id=order.id,
            invoice_number="INV-REPORT-1",
            subtotal=Decimal("400.00"),
            discount_type=DiscountType.NONE,
            discount_value=Decimal("0.00"),
            discount_amount=Decimal("0.00"),
            gst_percentage=Decimal("5.00"),
            gst_amount=Decimal("20.00"),
            grand_total=Decimal("420.00"),
            payment_method=PaymentMethod.UPI,
            payment_status=PaymentStatus.PAID,
            paid_at=datetime.now(
                timezone.utc
            ).replace(tzinfo=None),
        )
    )

    database.commit()


def test_staff_can_create_customer(
    database_session: Session,
) -> None:
    """Staff can create a customer record."""

    client, _ = build_client(
        database_session,
        UserRole.STAFF,
    )

    with client:
        response = client.post(
            "/api/v1/customers",
            json={
                "full_name": "Rahul Das",
                "phone": "9876543210",
                "email": "rahul@example.com",
                "address": "Jorhat",
                "notes": "Prefers window table",
                "is_active": True,
            },
        )

    clear_overrides()

    assert response.status_code == 201
    assert (
        response.json()["data"]["full_name"]
        == "Rahul Das"
    )


def test_duplicate_customer_phone_is_blocked(
    database_session: Session,
) -> None:
    """Customer phone numbers cannot be duplicated."""

    client, _ = build_client(database_session)

    payload = {
        "full_name": "First Customer",
        "phone": "9999999999",
        "email": None,
        "address": None,
        "notes": None,
        "is_active": True,
    }

    with client:
        first_response = client.post(
            "/api/v1/customers",
            json=payload,
        )

        payload["full_name"] = "Second Customer"

        second_response = client.post(
            "/api/v1/customers",
            json=payload,
        )

    clear_overrides()

    assert first_response.status_code == 201
    assert second_response.status_code == 409


def test_customer_detail_contains_paid_spending(
    database_session: Session,
) -> None:
    """Customer detail calculates paid spending."""

    client, user = build_client(database_session)

    with client:
        customer_response = client.post(
            "/api/v1/customers",
            json={
                "full_name": "Paid Customer",
                "phone": "8888888888",
                "email": None,
                "address": None,
                "notes": None,
                "is_active": True,
            },
        )

        customer_id = (
            customer_response.json()["data"]["id"]
        )

        create_paid_order(
            database_session,
            user,
            customer_id,
        )

        detail_response = client.get(
            f"/api/v1/customers/{customer_id}"
        )

    clear_overrides()

    assert detail_response.status_code == 200
    assert (
        detail_response.json()["data"][
            "total_paid_spending"
        ]
        == "420.00"
    )
    assert (
        detail_response.json()["data"][
            "completed_order_count"
        ]
        == 1
    )


def test_staff_can_read_dashboard(
    database_session: Session,
) -> None:
    """Staff can view dashboard totals."""

    client, _ = build_client(
        database_session,
        UserRole.STAFF,
    )

    with client:
        response = client.get(
            "/api/v1/reports/dashboard"
        )

    clear_overrides()

    assert response.status_code == 200
    assert "today_revenue" in response.json()["data"]


def test_reports_are_admin_only(
    database_session: Session,
) -> None:
    """Full reports are restricted to Admin."""

    staff_client, _ = build_client(
        database_session,
        UserRole.STAFF,
    )

    with staff_client:
        staff_response = staff_client.get(
            "/api/v1/reports/summary"
        )

    clear_overrides()

    admin_client, _ = build_client(
        database_session,
        UserRole.ADMIN,
    )

    with admin_client:
        admin_response = admin_client.get(
            "/api/v1/reports/summary"
        )

    clear_overrides()

    assert staff_response.status_code == 403
    assert admin_response.status_code == 200