"""Reservation business rules and database operations."""

from datetime import datetime, timezone
from secrets import token_hex

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.core.exceptions import AppException
from app.models.customer import Customer
from app.models.dining_table import DiningTable
from app.models.reservation import Reservation
from app.models.user import User
from app.schemas.reservation import (
    AvailabilitySearch,
    CustomerReservationCreate,
)
from app.utils.enums import ReservationStatus


BLOCKING_STATUSES = {
    ReservationStatus.PENDING,
    ReservationStatus.CONFIRMED,
    ReservationStatus.SEATED,
}

CUSTOMER_CANCELLABLE_STATUSES = {
    ReservationStatus.PENDING,
    ReservationStatus.CONFIRMED,
}


def normalise_datetime(value: datetime) -> datetime:
    """Convert aware datetimes to naive UTC for SQLite consistency."""

    if value.tzinfo is None:
        return value

    return value.astimezone(timezone.utc).replace(tzinfo=None)


def get_customer_for_user(
    database: Session,
    current_user: User,
) -> Customer:
    """Return the customer profile connected to a user."""

    statement = select(Customer).where(
        Customer.user_id == current_user.id,
        Customer.is_active.is_(True),
    )
    customer = database.scalar(statement)

    if customer is None:
        raise AppException(
            message="An active customer profile was not found.",
            status_code=404,
        )

    return customer


def find_available_tables(
    database: Session,
    search_data: AvailabilitySearch,
) -> list[DiningTable]:
    """Return active tables without an overlapping reservation."""

    start_time = normalise_datetime(search_data.start_time)
    end_time = normalise_datetime(search_data.end_time)

    overlapping_table_ids = select(
        Reservation.table_id
    ).where(
        Reservation.status.in_(BLOCKING_STATUSES),
        Reservation.start_time < end_time,
        Reservation.end_time > start_time,
    )

    statement = (
        select(DiningTable)
        .where(
            DiningTable.is_active.is_(True),
            DiningTable.capacity >= search_data.guest_count,
            DiningTable.id.not_in(overlapping_table_ids),
        )
        .order_by(
            DiningTable.capacity.asc(),
            DiningTable.area.asc(),
            DiningTable.table_number.asc(),
        )
    )

    return list(database.scalars(statement).all())


def table_is_available(
    database: Session,
    table_id: int,
    start_time: datetime,
    end_time: datetime,
    excluded_reservation_id: int | None = None,
) -> bool:
    """Check whether a table is free for a selected period."""

    normalised_start = normalise_datetime(start_time)
    normalised_end = normalise_datetime(end_time)

    statement = select(Reservation.id).where(
        Reservation.table_id == table_id,
        Reservation.status.in_(BLOCKING_STATUSES),
        Reservation.start_time < normalised_end,
        Reservation.end_time > normalised_start,
    )

    if excluded_reservation_id is not None:
        statement = statement.where(
            Reservation.id != excluded_reservation_id
        )

    return database.scalar(statement.limit(1)) is None


def generate_reservation_number(database: Session) -> str:
    """Generate a readable unique reservation number."""

    date_part = datetime.now(timezone.utc).strftime("%Y%m%d")

    for _ in range(10):
        reservation_number = (
            f"LB-RES-{date_part}-{token_hex(2).upper()}"
        )

        existing = database.scalar(
            select(Reservation.id).where(
                Reservation.reservation_number
                == reservation_number
            )
        )

        if existing is None:
            return reservation_number

    raise AppException(
        message="A reservation number could not be generated.",
        status_code=500,
    )


def create_customer_reservation(
    database: Session,
    current_user: User,
    reservation_data: CustomerReservationCreate,
) -> Reservation:
    """Create a pending reservation for a registered customer."""

    customer = get_customer_for_user(database, current_user)
    dining_table = database.get(
        DiningTable,
        reservation_data.table_id,
    )

    if dining_table is None or not dining_table.is_active:
        raise AppException(
            message="The selected table is not available.",
            status_code=404,
        )

    if dining_table.capacity < reservation_data.guest_count:
        raise AppException(
            message="The selected table is too small for this booking.",
            status_code=400,
        )

    start_time = normalise_datetime(
        reservation_data.start_time
    )
    end_time = normalise_datetime(
        reservation_data.end_time
    )

    current_time = datetime.now(timezone.utc).replace(tzinfo=None)

    if start_time <= current_time:
        raise AppException(
            message="Reservation time must be in the future.",
            status_code=400,
        )

    if not table_is_available(
        database=database,
        table_id=dining_table.id,
        start_time=start_time,
        end_time=end_time,
    ):
        raise AppException(
            message=(
                "The selected table was booked by another customer. "
                "Choose another available table."
            ),
            status_code=409,
        )

    reservation = Reservation(
        reservation_number=generate_reservation_number(database),
        customer_id=customer.id,
        table_id=dining_table.id,
        created_by_user_id=current_user.id,
        start_time=start_time,
        end_time=end_time,
        guest_count=reservation_data.guest_count,
        status=ReservationStatus.PENDING,
        notes=reservation_data.notes,
    )

    database.add(reservation)
    database.commit()

    return get_reservation(database, reservation.id)


def reservation_query():
    """Build the standard reservation query with related records."""

    return select(Reservation).options(
        joinedload(Reservation.table),
        joinedload(Reservation.customer),
    )


def get_reservation(
    database: Session,
    reservation_id: int,
) -> Reservation:
    """Return one reservation with table and customer details."""

    statement = reservation_query().where(
        Reservation.id == reservation_id
    )
    reservation = database.scalar(statement)

    if reservation is None:
        raise AppException(
            message="Reservation was not found.",
            status_code=404,
        )

    return reservation


def list_customer_reservations(
    database: Session,
    current_user: User,
) -> list[Reservation]:
    """Return reservations belonging to the signed-in customer."""

    customer = get_customer_for_user(database, current_user)

    statement = (
        reservation_query()
        .where(Reservation.customer_id == customer.id)
        .order_by(Reservation.start_time.desc())
    )

    return list(database.scalars(statement).unique().all())


def list_all_reservations(
    database: Session,
    status: ReservationStatus | None = None,
) -> list[Reservation]:
    """Return reservation records for Staff and Admin."""

    statement = reservation_query()

    if status is not None:
        statement = statement.where(
            Reservation.status == status
        )

    statement = statement.order_by(
        Reservation.start_time.asc()
    )

    return list(database.scalars(statement).unique().all())


def cancel_customer_reservation(
    database: Session,
    current_user: User,
    reservation_id: int,
    cancellation_reason: str | None,
) -> Reservation:
    """Cancel a reservation owned by the current customer."""

    customer = get_customer_for_user(database, current_user)
    reservation = get_reservation(database, reservation_id)

    if reservation.customer_id != customer.id:
        raise AppException(
            message="You cannot cancel this reservation.",
            status_code=403,
        )

    if reservation.status not in CUSTOMER_CANCELLABLE_STATUSES:
        raise AppException(
            message="This reservation can no longer be cancelled.",
            status_code=409,
        )

    current_time = datetime.now(timezone.utc).replace(tzinfo=None)

    if reservation.start_time <= current_time:
        raise AppException(
            message="A started reservation cannot be cancelled.",
            status_code=409,
        )

    reservation.status = ReservationStatus.CANCELLED
    reservation.cancellation_reason = cancellation_reason
    reservation.cancelled_at = current_time

    database.add(reservation)
    database.commit()

    return get_reservation(database, reservation.id)


def update_reservation_status(
    database: Session,
    reservation_id: int,
    new_status: ReservationStatus,
    cancellation_reason: str | None,
) -> Reservation:
    """Update reservation status as Staff or Admin."""

    reservation = get_reservation(database, reservation_id)

    if new_status == ReservationStatus.CANCELLED:
        reservation.cancelled_at = (
            datetime.now(timezone.utc).replace(tzinfo=None)
        )
        reservation.cancellation_reason = cancellation_reason
    else:
        reservation.cancelled_at = None
        reservation.cancellation_reason = None

    reservation.status = new_status

    database.add(reservation)
    database.commit()

    return get_reservation(database, reservation.id)