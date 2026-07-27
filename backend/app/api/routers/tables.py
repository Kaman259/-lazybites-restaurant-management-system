"""Dining table management endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.dependencies import DatabaseSession
from app.auth.permissions import (
    require_admin,
    require_staff_or_admin,
)
from app.core.responses import success_response
from app.models.user import User
from app.schemas.dining_table import (
    DiningTableCreate,
    DiningTableResponse,
    DiningTableUpdate,
)
from app.services.table_service import (
    create_dining_table,
    delete_dining_table,
    get_dining_table,
    list_dining_tables,
    update_dining_table,
)


router = APIRouter(
    prefix="/tables",
    tags=["Dining Tables"],
)

AdminUser = Annotated[User, Depends(require_admin)]
StaffUser = Annotated[User, Depends(require_staff_or_admin)]


@router.get("")
def read_dining_tables(
    database: DatabaseSession,
    current_user: StaffUser,
    include_inactive: bool = Query(default=True),
):
    """Return dining tables for Staff and Admin."""

    del current_user

    dining_tables = list_dining_tables(
        database=database,
        include_inactive=include_inactive,
    )

    response_data = [
        DiningTableResponse.model_validate(table).model_dump(
            mode="json"
        )
        for table in dining_tables
    ]

    return success_response(
        message="Dining tables retrieved successfully.",
        data=response_data,
    )


@router.post("", status_code=201)
def add_dining_table(
    table_data: DiningTableCreate,
    database: DatabaseSession,
    current_user: AdminUser,
):
    """Create a dining table."""

    del current_user

    dining_table = create_dining_table(
        database=database,
        table_data=table_data,
    )

    response_data = DiningTableResponse.model_validate(
        dining_table
    )

    return success_response(
        message="Dining table created successfully.",
        data=response_data.model_dump(mode="json"),
        status_code=201,
    )


@router.put("/{table_id}")
def edit_dining_table(
    table_id: int,
    table_data: DiningTableUpdate,
    database: DatabaseSession,
    current_user: AdminUser,
):
    """Update a dining table."""

    del current_user

    dining_table = get_dining_table(database, table_id)

    updated_table = update_dining_table(
        database=database,
        dining_table=dining_table,
        table_data=table_data,
    )

    response_data = DiningTableResponse.model_validate(
        updated_table
    )

    return success_response(
        message="Dining table updated successfully.",
        data=response_data.model_dump(mode="json"),
    )


@router.delete("/{table_id}")
def remove_dining_table(
    table_id: int,
    database: DatabaseSession,
    current_user: AdminUser,
):
    """Delete a table that has no history."""

    del current_user

    dining_table = get_dining_table(database, table_id)

    delete_dining_table(
        database=database,
        dining_table=dining_table,
    )

    return success_response(
        message="Dining table deleted successfully.",
        data=None,
    )