"""Tests for combined reservation billing."""

from collections.abc import Generator
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401
from app.core.exceptions import AppException
from app.database.base import Base
from app.models.customer import Customer
from app.models.dining_table import DiningTable
from app.models.invoice import Invoice
from app.models.menu_category import MenuCategory
from app.models.menu_item import MenuItem
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.reservation import Reservation
from app.models.restaurant_settings import (
    RestaurantSettings,
)
from app.models.user import User
from app.schemas.invoice import InvoiceCreate
from app.services.invoice_service import create_invoice
from app.utils.enums import (
    DiscountType,
    FoodType,
    OrderStatus,
    OrderType,
    ReservationStatus,
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


def create_settings(
    database: Session,
) -> RestaurantSettings:
    """Create restaurant settings required for billing."""

    settings = RestaurantSettings(
        restaurant_name="LazyBites",
        address="Test Address",
        phone="9999999999",
        email="lazybites@example.com",
        gstin=None,
        default_gst_percentage=Decimal("5.00"),
        currency="INR",
        invoice_prefix="INV",
        receipt_footer="Thank you.",
        logo_path=None,
        timezone="Asia/Kolkata",
    )

    database.add(settings)
    database.flush()

    return settings


def create_user(
    database: Session,
) -> User:
    """Create an Admin user used by test orders."""

    user = User(
        firebase_uid="billing-test-admin",
        full_name="Billing Admin",
        email="billing-admin@example.com",
        role=UserRole.ADMIN,
        is_active=True,
    )

    database.add(user)
    database.flush()

    return user


def create_customer(
    database: Session,
) -> Customer:
    """Create a customer for the reservation."""

    customer = Customer(
        user_id=None,
        full_name="Billing Customer",
        phone="8888888888",
        email="billing-customer@example.com",
        address="Test Address",
        notes=None,
        is_active=True,
    )

    database.add(customer)
    database.flush()

    return customer


def create_table(
    database: Session,
) -> DiningTable:
    """Create a dining table."""

    dining_table = DiningTable(
        table_number="BILL-T-01",
        capacity=4,
        area="Main Hall",
        description=None,
        is_active=True,
    )

    database.add(dining_table)
    database.flush()

    return dining_table


def create_menu_item(
    database: Session,
) -> MenuItem:
    """Create a menu item used by billing orders."""

    category = MenuCategory(
        name="Billing Category",
        description=None,
        display_order=1,
        is_active=True,
    )

    database.add(category)
    database.flush()

    menu_item = MenuItem(
        category_id=category.id,
        name="Billing Meal",
        description=None,
        price=Decimal("100.00"),
        food_type=FoodType.VEG,
        image_path=None,
        is_available=True,
        is_active=True,
    )

    database.add(menu_item)
    database.flush()

    return menu_item


def create_reservation(
    database: Session,
    user: User,
    customer: Customer,
    dining_table: DiningTable,
) -> Reservation:
    """Create a seated reservation."""

    now = (
        datetime.now(timezone.utc)
        .replace(tzinfo=None)
    )

    reservation = Reservation(
        reservation_number="LB-BILL-RES-001",
        customer_id=customer.id,
        table_id=dining_table.id,
        created_by_user_id=user.id,
        start_time=now,
        end_time=now + timedelta(hours=2),
        guest_count=2,
        status=ReservationStatus.SEATED,
        notes=None,
        cancellation_reason=None,
        cancelled_at=None,
    )

    database.add(reservation)
    database.flush()

    return reservation


def create_order(
    database: Session,
    *,
    order_number: str,
    user: User,
    customer: Customer,
    dining_table: DiningTable,
    reservation: Reservation,
    menu_item: MenuItem,
    quantity: int,
    status: OrderStatus,
) -> Order:
    """Create one order attached to the reservation."""

    now = (
        datetime.now(timezone.utc)
        .replace(tzinfo=None)
    )

    order = Order(
        order_number=order_number,
        customer_id=customer.id,
        table_id=dining_table.id,
        reservation_id=reservation.id,
        invoice_id=None,
        created_by_user_id=user.id,
        order_type=OrderType.DINE_IN,
        status=status,
        special_instructions=None,
        delivery_address=None,
        completed_at=(
            now
            if status == OrderStatus.COMPLETED
            else None
        ),
        cancelled_at=(
            now
            if status == OrderStatus.CANCELLED
            else None
        ),
        cancellation_reason=(
            "Cancelled during test"
            if status == OrderStatus.CANCELLED
            else None
        ),
    )

    database.add(order)
    database.flush()

    unit_price = Decimal("100.00")

    order_item = OrderItem(
        order_id=order.id,
        menu_item_id=menu_item.id,
        item_name=menu_item.name,
        unit_price=unit_price,
        quantity=quantity,
        special_instruction=None,
        line_total=(
            unit_price * quantity
        ),
    )

    database.add(order_item)
    database.flush()

    return order


def create_reservation_setup(
    database: Session,
    second_order_status: OrderStatus = (
        OrderStatus.COMPLETED
    ),
) -> tuple[Order, Order]:
    """Create two orders under the same reservation."""

    create_settings(database)

    user = create_user(database)
    customer = create_customer(database)
    dining_table = create_table(database)
    menu_item = create_menu_item(database)

    reservation = create_reservation(
        database=database,
        user=user,
        customer=customer,
        dining_table=dining_table,
    )

    first_order = create_order(
        database=database,
        order_number="LB-BILL-ORDER-001",
        user=user,
        customer=customer,
        dining_table=dining_table,
        reservation=reservation,
        menu_item=menu_item,
        quantity=2,
        status=OrderStatus.COMPLETED,
    )

    second_order = create_order(
        database=database,
        order_number="LB-BILL-ORDER-002",
        user=user,
        customer=customer,
        dining_table=dining_table,
        reservation=reservation,
        menu_item=menu_item,
        quantity=3,
        status=second_order_status,
    )

    database.commit()

    return first_order, second_order


def test_reservation_orders_generate_one_combined_invoice(
    database_session: Session,
) -> None:
    """Completed orders from one reservation share one invoice."""

    first_order, second_order = (
        create_reservation_setup(
            database_session
        )
    )

    invoice = create_invoice(
        database=database_session,
        invoice_data=InvoiceCreate(
            order_id=first_order.id,
            discount_type=DiscountType.NONE,
            discount_value=Decimal("0.00"),
        ),
    )

    assert len(invoice.orders) == 2

    assert {
        order.id
        for order in invoice.orders
    } == {
        first_order.id,
        second_order.id,
    }

    assert invoice.subtotal == Decimal("500.00")
    assert invoice.gst_amount == Decimal("25.00")
    assert invoice.grand_total == Decimal("525.00")

    database_session.refresh(first_order)
    database_session.refresh(second_order)

    assert first_order.invoice_id == invoice.id
    assert second_order.invoice_id == invoice.id


def test_combined_invoice_prevents_second_invoice(
    database_session: Session,
) -> None:
    """An order from an already billed reservation cannot be billed again."""

    first_order, second_order = (
        create_reservation_setup(
            database_session
        )
    )

    create_invoice(
        database=database_session,
        invoice_data=InvoiceCreate(
            order_id=first_order.id,
            discount_type=DiscountType.NONE,
            discount_value=Decimal("0.00"),
        ),
    )

    with pytest.raises(AppException):
        create_invoice(
            database=database_session,
            invoice_data=InvoiceCreate(
                order_id=second_order.id,
                discount_type=DiscountType.NONE,
                discount_value=Decimal("0.00"),
            ),
        )

    invoice_count = database_session.scalar(
        select(
            func.count(Invoice.id)
        )
    )

    assert invoice_count == 1


def test_active_reservation_order_blocks_final_invoice(
    database_session: Session,
) -> None:
    """Billing waits until every active reservation order is finished."""

    first_order, _ = (
        create_reservation_setup(
            database_session,
            second_order_status=OrderStatus.PENDING,
        )
    )

    with pytest.raises(AppException):
        create_invoice(
            database=database_session,
            invoice_data=InvoiceCreate(
                order_id=first_order.id,
                discount_type=DiscountType.NONE,
                discount_value=Decimal("0.00"),
            ),
        )

    invoice_count = database_session.scalar(
        select(
            func.count(Invoice.id)
        )
    )

    assert invoice_count == 0