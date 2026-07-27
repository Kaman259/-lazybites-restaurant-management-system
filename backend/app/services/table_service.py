"""Dining table service functions."""

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import AppException
from app.models.dining_table import DiningTable
from app.models.order import Order
from app.models.reservation import Reservation
from app.schemas.dining_table import (
    DiningTableCreate,
    DiningTableUpdate,
)


def list_dining_tables(
    database: Session,
    include_inactive: bool = True,
) -> list[DiningTable]:
    """Return dining tables ordered by area and table number."""

    statement = select(DiningTable)

    if not include_inactive:
        statement = statement.where(
            DiningTable.is_active.is_(True)
        )

    statement = statement.order_by(
        DiningTable.area.asc(),
        DiningTable.table_number.asc(),
    )

    return list(database.scalars(statement).all())


def get_dining_table(
    database: Session,
    table_id: int,
) -> DiningTable:
    """Return one dining table or raise a clear error."""

    dining_table = database.get(DiningTable, table_id)

    if dining_table is None:
        raise AppException(
            message="Dining table was not found.",
            status_code=404,
        )

    return dining_table


def create_dining_table(
    database: Session,
    table_data: DiningTableCreate,
) -> DiningTable:
    """Create a dining table with a unique table number."""

    existing_statement = select(DiningTable).where(
        func.lower(DiningTable.table_number)
        == table_data.table_number.lower()
    )
    existing_table = database.scalar(existing_statement)

    if existing_table is not None:
        raise AppException(
            message="A table with this number already exists.",
            status_code=409,
        )

    dining_table = DiningTable(
        **table_data.model_dump(),
    )

    database.add(dining_table)

    try:
        database.commit()
    except IntegrityError as error:
        database.rollback()
        raise AppException(
            message="The dining table could not be created.",
            status_code=409,
        ) from error

    database.refresh(dining_table)
    return dining_table


def update_dining_table(
    database: Session,
    dining_table: DiningTable,
    table_data: DiningTableUpdate,
) -> DiningTable:
    """Update an existing dining table."""

    duplicate_statement = select(DiningTable).where(
        func.lower(DiningTable.table_number)
        == table_data.table_number.lower(),
        DiningTable.id != dining_table.id,
    )
    duplicate_table = database.scalar(duplicate_statement)

    if duplicate_table is not None:
        raise AppException(
            message="A table with this number already exists.",
            status_code=409,
        )

    for field_name, field_value in table_data.model_dump().items():
        setattr(dining_table, field_name, field_value)

    database.add(dining_table)

    try:
        database.commit()
    except IntegrityError as error:
        database.rollback()
        raise AppException(
            message="The dining table could not be updated.",
            status_code=409,
        ) from error

    database.refresh(dining_table)
    return dining_table


def delete_dining_table(
    database: Session,
    dining_table: DiningTable,
) -> None:
    """Delete an unused table."""

    reservation_count = database.scalar(
        select(func.count(Reservation.id)).where(
            Reservation.table_id == dining_table.id
        )
    )

    order_count = database.scalar(
        select(func.count(Order.id)).where(
            Order.table_id == dining_table.id
        )
    )

    if reservation_count or order_count:
        raise AppException(
            message=(
                "This table has reservation or order history. "
                "Disable it instead of deleting it."
            ),
            status_code=409,
        )

    database.delete(dining_table)
    database.commit()