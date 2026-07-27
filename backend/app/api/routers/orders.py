"""Restaurant order endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.dependencies import DatabaseSession
from app.auth.permissions import require_staff_or_admin
from app.core.responses import success_response
from app.models.user import User
from app.schemas.order import (
    OrderCreate,
    OrderResponse,
    OrderStatusUpdate,
)
from app.services.order_service import (
    calculate_order_subtotal,
    create_order,
    get_order,
    list_orders,
    update_order_status,
)
from app.utils.enums import OrderStatus, OrderType


router = APIRouter(
    prefix="/orders",
    tags=["Orders"],
)

StaffUser = Annotated[
    User,
    Depends(require_staff_or_admin),
]


def serialise_order(order):
    """Convert an order into API response data."""

    order_data = OrderResponse.model_validate(
        {
            **order.__dict__,
            "items": order.items,
            "customer": order.customer,
            "table": order.table,
            "reservation": order.reservation,
            "subtotal": calculate_order_subtotal(order),
        }
    )

    return order_data.model_dump(mode="json")


@router.post("", status_code=201)
def add_order(
    order_data: OrderCreate,
    database: DatabaseSession,
    current_user: StaffUser,
):
    """Create a dine-in, takeaway, or delivery order."""

    order = create_order(
        database=database,
        current_user=current_user,
        order_data=order_data,
    )

    return success_response(
        message="Order created successfully.",
        data=serialise_order(order),
        status_code=201,
    )


@router.get("")
def read_orders(
    database: DatabaseSession,
    current_user: StaffUser,
    status: OrderStatus | None = Query(default=None),
    order_type: OrderType | None = Query(default=None),
):
    """Return filtered restaurant orders."""

    del current_user

    orders = list_orders(
        database=database,
        status=status,
        order_type=order_type,
    )

    return success_response(
        message="Orders retrieved successfully.",
        data=[
            serialise_order(order)
            for order in orders
        ],
    )


@router.get("/{order_id}")
def read_order(
    order_id: int,
    database: DatabaseSession,
    current_user: StaffUser,
):
    """Return one restaurant order."""

    del current_user

    order = get_order(database, order_id)

    return success_response(
        message="Order retrieved successfully.",
        data=serialise_order(order),
    )


@router.patch("/{order_id}/status")
def change_order_status(
    order_id: int,
    status_data: OrderStatusUpdate,
    database: DatabaseSession,
    current_user: StaffUser,
):
    """Change an order's workflow status."""

    del current_user

    order = update_order_status(
        database=database,
        order_id=order_id,
        new_status=status_data.status,
        cancellation_reason=(
            status_data.cancellation_reason
        ),
    )

    return success_response(
        message="Order status updated successfully.",
        data=serialise_order(order),
    )