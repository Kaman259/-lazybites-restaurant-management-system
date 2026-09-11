"""Customer management and activity service functions."""

from decimal import Decimal

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, joinedload

from app.core.exceptions import AppException
from app.models.customer import Customer
from app.models.invoice import Invoice
from app.models.order import Order
from app.models.reservation import Reservation
from app.schemas.customer_management import (
    CustomerCreate,
    CustomerUpdate,
)
from app.utils.enums import (
    OrderStatus,
    PaymentStatus,
)


def money(value: Decimal | int | float | None) -> Decimal:
    """Return a two-decimal monetary value."""

    return Decimal(value or 0).quantize(
        Decimal("0.01")
    )


def customer_statistics_subqueries():
    """Build reusable customer-statistics subqueries."""

    reservation_count = (
        select(func.count(Reservation.id))
        .where(
            Reservation.customer_id == Customer.id
        )
        .correlate(Customer)
        .scalar_subquery()
    )

    order_count = (
        select(func.count(Order.id))
        .where(
            Order.customer_id == Customer.id
        )
        .correlate(Customer)
        .scalar_subquery()
    )

    completed_order_count = (
        select(func.count(Order.id))
        .where(
            Order.customer_id == Customer.id,
            Order.status == OrderStatus.COMPLETED,
        )
        .correlate(Customer)
        .scalar_subquery()
    )

    customer_invoice_ids = (
        select(Order.invoice_id)
        .where(
            Order.customer_id == Customer.id,
            Order.invoice_id.is_not(None),
        )
        .distinct()
        .correlate(Customer)
    )

    total_paid_spending = (
        select(
            func.coalesce(
                func.sum(Invoice.grand_total),
                0,
            )
        )
        .where(
            Invoice.id.in_(customer_invoice_ids),
            Invoice.payment_status
            == PaymentStatus.PAID,
        )
        .correlate(Customer)
        .scalar_subquery()
    )

    return (
        reservation_count,
        order_count,
        completed_order_count,
        total_paid_spending,
    )


def serialise_customer_summary(
    customer: Customer,
    reservation_count: int,
    order_count: int,
    completed_order_count: int,
    total_paid_spending: Decimal,
) -> dict:
    """Build customer summary data."""

    return {
        "id": customer.id,
        "user_id": customer.user_id,
        "full_name": customer.full_name,
        "phone": customer.phone,
        "email": customer.email,
        "address": customer.address,
        "notes": customer.notes,
        "is_active": customer.is_active,
        "created_at": customer.created_at,
        "updated_at": customer.updated_at,
        "reservation_count": reservation_count,
        "order_count": order_count,
        "completed_order_count": (
            completed_order_count
        ),
        "total_paid_spending": money(
            total_paid_spending
        ),
    }


def list_customers(
    database: Session,
    search: str | None = None,
    include_inactive: bool = True,
) -> list[dict]:
    """Return searchable customer summaries."""

    (
        reservation_count,
        order_count,
        completed_order_count,
        total_paid_spending,
    ) = customer_statistics_subqueries()

    statement = select(
        Customer,
        reservation_count.label(
            "reservation_count"
        ),
        order_count.label(
            "order_count"
        ),
        completed_order_count.label(
            "completed_order_count"
        ),
        total_paid_spending.label(
            "total_paid_spending"
        ),
    )

    if not include_inactive:
        statement = statement.where(
            Customer.is_active.is_(True)
        )

    if search and search.strip():
        search_value = (
            f"%{search.strip().lower()}%"
        )

        statement = statement.where(
            or_(
                func.lower(
                    Customer.full_name
                ).like(search_value),
                func.lower(
                    Customer.phone
                ).like(search_value),
                func.lower(
                    func.coalesce(
                        Customer.email,
                        "",
                    )
                ).like(search_value),
            )
        )

    statement = statement.order_by(
        Customer.created_at.desc()
    )

    rows = database.execute(statement).all()

    return [
        serialise_customer_summary(
            customer=row[0],
            reservation_count=row[1],
            order_count=row[2],
            completed_order_count=row[3],
            total_paid_spending=row[4],
        )
        for row in rows
    ]


def get_customer(
    database: Session,
    customer_id: int,
) -> Customer:
    """Return one customer."""

    customer = database.get(
        Customer,
        customer_id,
    )

    if customer is None:
        raise AppException(
            message="Customer was not found.",
            status_code=404,
        )

    return customer


def ensure_unique_customer_phone(
    database: Session,
    phone: str,
    excluded_customer_id: int | None = None,
) -> None:
    """Prevent duplicate customer phone records."""

    statement = select(
        Customer.id
    ).where(
        func.lower(Customer.phone)
        == phone.strip().lower()
    )

    if excluded_customer_id is not None:
        statement = statement.where(
            Customer.id != excluded_customer_id
        )

    if database.scalar(statement) is not None:
        raise AppException(
            message=(
                "A customer with this phone number "
                "already exists."
            ),
            status_code=409,
        )


def create_customer(
    database: Session,
    customer_data: CustomerCreate,
) -> Customer:
    """Create a staff-managed customer."""

    ensure_unique_customer_phone(
        database,
        customer_data.phone,
    )

    customer = Customer(
        user_id=None,
        **customer_data.model_dump(),
    )

    database.add(customer)
    database.commit()
    database.refresh(customer)

    return customer


def update_customer(
    database: Session,
    customer: Customer,
    customer_data: CustomerUpdate,
) -> Customer:
    """Update customer information."""

    ensure_unique_customer_phone(
        database=database,
        phone=customer_data.phone,
        excluded_customer_id=customer.id,
    )

    for field_name, field_value in (
        customer_data.model_dump().items()
    ):
        setattr(
            customer,
            field_name,
            field_value,
        )

    database.add(customer)
    database.commit()
    database.refresh(customer)

    return customer


def update_customer_status(
    database: Session,
    customer: Customer,
    is_active: bool,
) -> Customer:
    """Activate or deactivate a customer."""

    customer.is_active = is_active

    database.add(customer)
    database.commit()
    database.refresh(customer)

    return customer


def get_customer_detail(
    database: Session,
    customer_id: int,
) -> dict:
    """Return a customer with reservations and orders."""

    customer = get_customer(
        database,
        customer_id,
    )

    (
        reservation_count,
        order_count,
        completed_order_count,
        total_paid_spending,
    ) = customer_statistics_subqueries()

    summary_row = database.execute(
        select(
            reservation_count,
            order_count,
            completed_order_count,
            total_paid_spending,
        ).where(
            Customer.id == customer.id
        )
    ).one()

    reservation_statement = (
        select(Reservation)
        .options(
            joinedload(
                Reservation.table
            )
        )
        .where(
            Reservation.customer_id
            == customer.id
        )
        .order_by(
            Reservation.start_time.desc()
        )
        .limit(20)
    )

    reservations = list(
        database.scalars(
            reservation_statement
        ).all()
    )

    order_statement = (
        select(Order)
        .options(
            joinedload(Order.invoice)
        )
        .where(
            Order.customer_id == customer.id
        )
        .order_by(
            Order.created_at.desc()
        )
        .limit(20)
    )

    orders = list(
        database.scalars(
            order_statement
        ).all()
    )

    response_data = serialise_customer_summary(
        customer=customer,
        reservation_count=summary_row[0],
        order_count=summary_row[1],
        completed_order_count=summary_row[2],
        total_paid_spending=summary_row[3],
    )

    response_data["reservations"] = [
        {
            "id": reservation.id,
            "reservation_number": (
                reservation.reservation_number
            ),
            "start_time": reservation.start_time,
            "end_time": reservation.end_time,
            "guest_count": reservation.guest_count,
            "status": reservation.status,
            "table_number": (
                reservation.table.table_number
            ),
        }
        for reservation in reservations
    ]

    response_data["orders"] = [
        {
            "id": order.id,
            "order_number": order.order_number,
            "order_type": order.order_type,
            "status": order.status,
            "created_at": order.created_at,
            "invoice_number": (
                order.invoice.invoice_number
                if order.invoice
                else None
            ),
            "payment_status": (
                order.invoice.payment_status
                if order.invoice
                else None
            ),
            "grand_total": (
                money(
                    order.invoice.grand_total
                )
                if order.invoice
                else None
            ),
        }
        for order in orders
    ]

    return response_data