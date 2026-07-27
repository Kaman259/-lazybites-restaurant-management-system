"""Tests for invoice generation and payment handling."""

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
from app.models.menu_category import MenuCategory
from app.models.menu_item import MenuItem
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.user import User
from app.utils.enums import (
    FoodType,
    OrderStatus,
    OrderType,
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
    database_session: Session,
) -> tuple[TestClient, User]:
    """Create an authenticated Admin test client."""

    user = User(
        firebase_uid="invoice-test-admin",
        full_name="Invoice Admin",
        email="invoice-admin@example.com",
        role=UserRole.ADMIN,
        is_active=True,
    )

    database_session.add(user)
    database_session.commit()

    def override_get_db():
        yield database_session

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
    """Clear test dependency overrides."""

    fastapi_app.dependency_overrides.clear()


def create_completed_order(
    database: Session,
    user: User,
) -> Order:
    """Create a completed order for invoice testing."""

    category = MenuCategory(
        name="Invoice Test Category",
        description=None,
        display_order=1,
        is_active=True,
    )

    database.add(category)
    database.flush()

    menu_item = MenuItem(
        category_id=category.id,
        name="Invoice Test Meal",
        description=None,
        price="200.00",
        food_type=FoodType.VEG,
        image_path=None,
        is_available=True,
        is_active=True,
    )

    database.add(menu_item)
    database.flush()

    order = Order(
        order_number="LB-ORD-INVOICE-001",
        customer_id=None,
        table_id=None,
        reservation_id=None,
        created_by_user_id=user.id,
        order_type=OrderType.TAKEAWAY,
        status=OrderStatus.COMPLETED,
        special_instructions=None,
        delivery_address=None,
    )

    database.add(order)
    database.flush()

    order_item = OrderItem(
        order_id=order.id,
        menu_item_id=menu_item.id,
        item_name=menu_item.name,
        unit_price="200.00",
        quantity=2,
        special_instruction=None,
        line_total="400.00",
    )

    database.add(order_item)
    database.commit()
    database.refresh(order)

    return order


def test_invoice_calculates_gst(
    database_session: Session,
) -> None:
    """Invoice calculates GST using restaurant settings."""

    client, user = build_client(database_session)
    order = create_completed_order(database_session, user)

    with client:
        response = client.post(
            "/api/v1/invoices",
            json={
                "order_id": order.id,
                "discount_type": "NONE",
                "discount_value": "0.00",
            },
        )

    clear_overrides()

    assert response.status_code == 201
    assert response.json()["data"]["subtotal"] == "400.00"
    assert response.json()["data"]["gst_amount"] == "20.00"
    assert response.json()["data"]["grand_total"] == "420.00"
    assert (
        response.json()["data"]["payment_status"]
        == "UNPAID"
    )


def test_percentage_discount_is_calculated(
    database_session: Session,
) -> None:
    """Percentage discount is calculated before GST."""

    client, user = build_client(database_session)
    order = create_completed_order(database_session, user)

    with client:
        response = client.post(
            "/api/v1/invoices",
            json={
                "order_id": order.id,
                "discount_type": "PERCENTAGE",
                "discount_value": "10.00",
            },
        )

    clear_overrides()

    assert response.status_code == 201
    assert (
        response.json()["data"]["discount_amount"]
        == "40.00"
    )
    assert response.json()["data"]["gst_amount"] == "18.00"
    assert response.json()["data"]["grand_total"] == "378.00"


def test_duplicate_invoice_is_blocked(
    database_session: Session,
) -> None:
    """An order can have only one invoice."""

    client, user = build_client(database_session)
    order = create_completed_order(database_session, user)

    payload = {
        "order_id": order.id,
        "discount_type": "NONE",
        "discount_value": "0.00",
    }

    with client:
        first_response = client.post(
            "/api/v1/invoices",
            json=payload,
        )

        second_response = client.post(
            "/api/v1/invoices",
            json=payload,
        )

    clear_overrides()

    assert first_response.status_code == 201
    assert second_response.status_code == 409


def test_invoice_can_be_paid(
    database_session: Session,
) -> None:
    """An unpaid invoice can be marked as paid."""

    client, user = build_client(database_session)
    order = create_completed_order(database_session, user)

    with client:
        create_response = client.post(
            "/api/v1/invoices",
            json={
                "order_id": order.id,
                "discount_type": "NONE",
                "discount_value": "0.00",
            },
        )

        invoice_id = create_response.json()["data"]["id"]

        payment_response = client.patch(
            f"/api/v1/invoices/{invoice_id}/payment",
            json={
                "payment_method": "UPI",
            },
        )

    clear_overrides()

    assert payment_response.status_code == 200
    assert (
        payment_response.json()["data"]["payment_status"]
        == "PAID"
    )
    assert (
        payment_response.json()["data"]["payment_method"]
        == "UPI"
    )
    assert payment_response.json()["data"]["paid_at"] is not None


def test_paid_invoice_can_be_refunded(
    database_session: Session,
) -> None:
    """A paid invoice can be refunded with a reason."""

    client, user = build_client(database_session)
    order = create_completed_order(database_session, user)

    with client:
        create_response = client.post(
            "/api/v1/invoices",
            json={
                "order_id": order.id,
                "discount_type": "NONE",
                "discount_value": "0.00",
            },
        )

        invoice_id = create_response.json()["data"]["id"]

        client.patch(
            f"/api/v1/invoices/{invoice_id}/payment",
            json={
                "payment_method": "CASH",
            },
        )

        refund_response = client.patch(
            f"/api/v1/invoices/{invoice_id}/refund",
            json={
                "refund_reason": "Customer order complaint",
            },
        )

    clear_overrides()

    assert refund_response.status_code == 200
    assert (
        refund_response.json()["data"]["payment_status"]
        == "REFUNDED"
    )
    assert (
        refund_response.json()["data"]["refund_reason"]
        == "Customer order complaint"
    )
    assert (
        refund_response.json()["data"]["refunded_at"]
        is not None
    )