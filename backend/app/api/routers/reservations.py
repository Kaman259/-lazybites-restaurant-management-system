"""Customer and staff reservation endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.dependencies import DatabaseSession, get_current_user
from app.auth.permissions import require_staff_or_admin
from app.core.responses import success_response
from app.models.user import User
from app.schemas.dining_table import AvailableTableResponse
from app.schemas.reservation import (
    AvailabilitySearch,
    CustomerReservationCreate,
    ReservationCancelRequest,
    ReservationResponse,
    ReservationStatusUpdate,
)
from app.services.reservation_service import (
    cancel_customer_reservation,
    create_customer_reservation,
    find_available_tables,
    list_all_reservations,
    list_customer_reservations,
    update_reservation_status,
)
from app.utils.enums import ReservationStatus


router = APIRouter(
    prefix="/reservations",
    tags=["Reservations"],
)

AuthenticatedUser = Annotated[
    User,
    Depends(get_current_user),
]

StaffUser = Annotated[
    User,
    Depends(require_staff_or_admin),
]


def serialise_reservation(reservation):
    """Convert one reservation into API response data."""

    return ReservationResponse.model_validate(
        reservation
    ).model_dump(mode="json")


@router.post("/availability")
def search_available_tables(
    search_data: AvailabilitySearch,
    database: DatabaseSession,
    current_user: AuthenticatedUser,
):
    """Return tables available for the selected period."""

    del current_user

    available_tables = find_available_tables(
        database=database,
        search_data=search_data,
    )

    response_data = [
        AvailableTableResponse.model_validate(table).model_dump(
            mode="json"
        )
        for table in available_tables
    ]

    return success_response(
        message="Available tables retrieved successfully.",
        data=response_data,
    )


@router.post("", status_code=201)
def add_customer_reservation(
    reservation_data: CustomerReservationCreate,
    database: DatabaseSession,
    current_user: AuthenticatedUser,
):
    """Create a customer reservation."""

    reservation = create_customer_reservation(
        database=database,
        current_user=current_user,
        reservation_data=reservation_data,
    )

    return success_response(
        message="Reservation created successfully.",
        data=serialise_reservation(reservation),
        status_code=201,
    )


@router.get("/me")
def read_my_reservations(
    database: DatabaseSession,
    current_user: AuthenticatedUser,
):
    """Return reservations belonging to the signed-in customer."""

    reservations = list_customer_reservations(
        database=database,
        current_user=current_user,
    )

    return success_response(
        message="Your reservations were retrieved successfully.",
        data=[
            serialise_reservation(reservation)
            for reservation in reservations
        ],
    )


@router.patch("/{reservation_id}/cancel")
def cancel_my_reservation(
    reservation_id: int,
    cancel_data: ReservationCancelRequest,
    database: DatabaseSession,
    current_user: AuthenticatedUser,
):
    """Cancel a reservation belonging to the signed-in customer."""

    reservation = cancel_customer_reservation(
        database=database,
        current_user=current_user,
        reservation_id=reservation_id,
        cancellation_reason=cancel_data.cancellation_reason,
    )

    return success_response(
        message="Reservation cancelled successfully.",
        data=serialise_reservation(reservation),
    )


@router.get("")
def read_all_reservations(
    database: DatabaseSession,
    current_user: StaffUser,
    status: ReservationStatus | None = Query(default=None),
):
    """Return reservations for restaurant staff."""

    del current_user

    reservations = list_all_reservations(
        database=database,
        status=status,
    )

    return success_response(
        message="Reservations retrieved successfully.",
        data=[
            serialise_reservation(reservation)
            for reservation in reservations
        ],
    )


@router.patch("/{reservation_id}/status")
def change_reservation_status(
    reservation_id: int,
    status_data: ReservationStatusUpdate,
    database: DatabaseSession,
    current_user: StaffUser,
):
    """Change a reservation status as Staff or Admin."""

    del current_user

    reservation = update_reservation_status(
        database=database,
        reservation_id=reservation_id,
        new_status=status_data.status,
        cancellation_reason=status_data.cancellation_reason,
    )

    return success_response(
        message="Reservation status updated successfully.",
        data=serialise_reservation(reservation),
    )