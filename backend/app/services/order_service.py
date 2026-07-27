"""Order business rules and database operations."""

from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from secrets import token_hex

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.core.exceptions import AppException
from app.models.customer import Customer
from app.models.dining_table import DiningTable
from app.models.menu_item import MenuItem
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.reservation import Reservation
from app.models.user import User
from app.schemas.order import OrderCreate
from app.utils.enums import (
    OrderStatus,
    OrderType,
    ReservationStatus,
)


MONEY_PLACES = Decimal("0.01")


ORDER_STATUS_TRANSITIONS = {
    OrderStatus.PENDING: {
        OrderStatus.PREPARING,
        OrderStatus.CANCELLED,
    },
    OrderStatus.PREPARING: {
        OrderStatus.READY,
        OrderStatus.CANCELLED,
    },
    OrderStatus.READY: {
        OrderStatus.SERVED,
        OrderStatus.COMPLETED,
        OrderStatus.CANCELLED,
    },
    OrderStatus.SERVED: {
        OrderStatus.COMPLETED,
    },
    OrderStatus.COMPLETED: set(),
    OrderStatus.CANCELLED: set(),
}


def money(value: Decimal) -> Decimal:
    """Round a monetary value to two decimal places."""

    return value.quantize(
        MONEY_PLACES,
        rounding=ROUND_HALF_UP,
    )


def order_query():
    """Build the standard order query with related records."""

    return select(Order).options(
        joinedload(Order.items),
        joinedload(Order.customer),
        joinedload(Order.table),
        joinedload(Order.reservation),
    )


def get_order(
    database: Session,
    order_id: int,
) -> Order:
    """Return one order with related information."""

    statement = order_query().where(
        Order.id == order_id
    )

    result = database.execute(statement)
    order = result.unique().scalar_one_or_none()

    if order is None:
        raise AppException(
            message="Order was not found.",
            status_code=404,
        )

    return order


def calculate_order_subtotal(order: Order) -> Decimal:
    """Calculate the subtotal using stored order-item totals."""

    subtotal = sum(
        (
            Decimal(order_item.line_total)
            for order_item in order.items
        ),
        Decimal("0.00"),
    )

    return money(subtotal)


def generate_order_number(database: Session) -> str:
    """Generate a readable unique order number."""

    date_part = datetime.now(timezone.utc).strftime("%Y%m%d")

    for _ in range(10):
        order_number = (
            f"LB-ORD-{date_part}-{token_hex(2).upper()}"
        )

        existing_order_id = database.scalar(
            select(Order.id).where(
                Order.order_number == order_number
            )
        )

        if existing_order_id is None:
            return order_number

    raise AppException(
        message="An order number could not be generated.",
        status_code=500,
    )


def validate_customer(
    database: Session,
    customer_id: int | None,
) -> Customer | None:
    """Return the selected active customer when provided."""

    if customer_id is None:
        return None

    customer = database.get(Customer, customer_id)

    if customer is None or not customer.is_active:
        raise AppException(
            message="The selected customer was not found.",
            status_code=404,
        )

    return customer


def validate_table(
    database: Session,
    table_id: int | None,
) -> DiningTable | None:
    """Return the selected active table when provided."""

    if table_id is None:
        return None

    dining_table = database.get(DiningTable, table_id)

    if dining_table is None or not dining_table.is_active:
        raise AppException(
            message="The selected dining table was not found.",
            status_code=404,
        )

    return dining_table


def validate_reservation(
    database: Session,
    reservation_id: int | None,
) -> Reservation | None:
    """Return a reservation that can be linked to an order."""

    if reservation_id is None:
        return None

    reservation = database.get(
        Reservation,
        reservation_id,
    )

    if reservation is None:
        raise AppException(
            message="The selected reservation was not found.",
            status_code=404,
        )

    if reservation.status not in {
        ReservationStatus.CONFIRMED,
        ReservationStatus.SEATED,
    }:
        raise AppException(
            message=(
                "Only confirmed or seated reservations "
                "can be linked to an order."
            ),
            status_code=409,
        )

    existing_order = database.scalar(
        select(Order.id).where(
            Order.reservation_id == reservation.id
        )
    )

    if existing_order is not None:
        raise AppException(
            message="This reservation already has an order.",
            status_code=409,
        )

    return reservation


def validate_order_type(
    order_data: OrderCreate,
) -> None:
    """Validate fields required by each order type."""

    if (
        order_data.order_type == OrderType.DINE_IN
        and order_data.table_id is None
    ):
        raise AppException(
            message="A dining table is required for a dine-in order.",
            status_code=400,
        )

    if (
        order_data.order_type
        in {
            OrderType.TAKEAWAY,
            OrderType.DELIVERY,
        }
        and order_data.table_id is not None
    ):
        raise AppException(
            message=(
                "A table cannot be assigned to a takeaway "
                "or delivery order."
            ),
            status_code=400,
        )

    if (
        order_data.order_type == OrderType.DELIVERY
        and not order_data.delivery_address
    ):
        raise AppException(
            message="A delivery address is required.",
            status_code=400,
        )

    if (
        order_data.order_type != OrderType.DELIVERY
        and order_data.delivery_address
    ):
        raise AppException(
            message=(
                "A delivery address can only be used "
                "for a delivery order."
            ),
            status_code=400,
        )

    if (
        order_data.reservation_id is not None
        and order_data.order_type != OrderType.DINE_IN
    ):
        raise AppException(
            message=(
                "A reservation can only be linked "
                "to a dine-in order."
            ),
            status_code=400,
        )


def load_order_menu_items(
    database: Session,
    order_data: OrderCreate,
) -> dict[int, MenuItem]:
    """Load and validate all requested menu items."""

    item_ids = {
        item.menu_item_id
        for item in order_data.items
    }

    if len(item_ids) != len(order_data.items):
        raise AppException(
            message=(
                "The same menu item cannot appear twice. "
                "Increase its quantity instead."
            ),
            status_code=400,
        )

    statement = (
        select(MenuItem)
        .options(joinedload(MenuItem.category))
        .where(MenuItem.id.in_(item_ids))
    )

    menu_items = list(database.scalars(statement).all())

    menu_item_map = {
        menu_item.id: menu_item
        for menu_item in menu_items
    }

    if len(menu_item_map) != len(item_ids):
        raise AppException(
            message="One or more selected menu items were not found.",
            status_code=404,
        )

    for menu_item in menu_items:
        if not menu_item.is_active:
            raise AppException(
                message=(
                    f"{menu_item.name} is currently disabled."
                ),
                status_code=409,
            )

        if not menu_item.is_available:
            raise AppException(
                message=(
                    f"{menu_item.name} is currently unavailable."
                ),
                status_code=409,
            )

        if not menu_item.category.is_active:
            raise AppException(
                message=(
                    f"The category for {menu_item.name} "
                    "is currently disabled."
                ),
                status_code=409,
            )

    return menu_item_map


def create_order(
    database: Session,
    current_user: User,
    order_data: OrderCreate,
) -> Order:
    """Create a restaurant order and snapshot item prices."""

    validate_order_type(order_data)

    customer = validate_customer(
        database,
        order_data.customer_id,
    )

    dining_table = validate_table(
        database,
        order_data.table_id,
    )

    reservation = validate_reservation(
        database,
        order_data.reservation_id,
    )

    if reservation is not None:
        if (
            dining_table is not None
            and reservation.table_id != dining_table.id
        ):
            raise AppException(
                message=(
                    "The selected table does not match "
                    "the reservation table."
                ),
                status_code=409,
            )

        if dining_table is None:
            dining_table = reservation.table

        if (
            customer is not None
            and reservation.customer_id != customer.id
        ):
            raise AppException(
                message=(
                    "The selected customer does not match "
                    "the reservation customer."
                ),
                status_code=409,
            )

        if customer is None:
            customer = reservation.customer

    menu_item_map = load_order_menu_items(
        database,
        order_data,
    )

    order = Order(
        order_number=generate_order_number(database),
        customer_id=customer.id if customer else None,
        table_id=dining_table.id if dining_table else None,
        reservation_id=(
            reservation.id if reservation else None
        ),
        created_by_user_id=current_user.id,
        order_type=order_data.order_type,
        status=OrderStatus.PENDING,
        special_instructions=(
            order_data.special_instructions
        ),
        delivery_address=order_data.delivery_address,
    )

    database.add(order)
    database.flush()

    for submitted_item in order_data.items:
        menu_item = menu_item_map[
            submitted_item.menu_item_id
        ]

        unit_price = money(
            Decimal(menu_item.price)
        )

        line_total = money(
            unit_price * submitted_item.quantity
        )

        order_item = OrderItem(
            order_id=order.id,
            menu_item_id=menu_item.id,
            item_name=menu_item.name,
            unit_price=unit_price,
            quantity=submitted_item.quantity,
            special_instruction=(
                submitted_item.special_instruction
            ),
            line_total=line_total,
        )

        database.add(order_item)

    database.commit()

    return get_order(database, order.id)


def list_orders(
    database: Session,
    status: OrderStatus | None = None,
    order_type: OrderType | None = None,
) -> list[Order]:
    """Return filtered orders, newest first."""

    statement = order_query()

    if status is not None:
        statement = statement.where(
            Order.status == status
        )

    if order_type is not None:
        statement = statement.where(
            Order.order_type == order_type
        )

    statement = statement.order_by(
        Order.created_at.desc()
    )

    result = database.execute(statement)

    return list(
        result.unique().scalars().all()
    )


def update_order_status(
    database: Session,
    order_id: int,
    new_status: OrderStatus,
    cancellation_reason: str | None,
) -> Order:
    """Move an order through its allowed status workflow."""

    order = get_order(database, order_id)

    if new_status == order.status:
        return order

    allowed_statuses = ORDER_STATUS_TRANSITIONS[
        order.status
    ]

    if new_status not in allowed_statuses:
        raise AppException(
            message=(
                f"Order cannot move from {order.status.value} "
                f"to {new_status.value}."
            ),
            status_code=409,
        )

    current_time = (
        datetime.now(timezone.utc)
        .replace(tzinfo=None)
    )

    if new_status == OrderStatus.CANCELLED:
        if not cancellation_reason:
            raise AppException(
                message="A cancellation reason is required.",
                status_code=400,
            )

        order.cancelled_at = current_time
        order.cancellation_reason = cancellation_reason
        order.completed_at = None

    elif new_status == OrderStatus.COMPLETED:
        order.completed_at = current_time
        order.cancelled_at = None
        order.cancellation_reason = None

    else:
        order.completed_at = None
        order.cancelled_at = None
        order.cancellation_reason = None

    order.status = new_status

    database.add(order)
    database.commit()

    return get_order(database, order.id)