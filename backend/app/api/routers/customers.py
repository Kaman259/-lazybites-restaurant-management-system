"""Staff customer-management endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.dependencies import DatabaseSession
from app.auth.permissions import require_staff_or_admin
from app.core.responses import success_response
from app.models.user import User
from app.schemas.customer_management import (
    CustomerCreate,
    CustomerDetailResponse,
    CustomerStatusUpdate,
    CustomerSummaryResponse,
    CustomerUpdate,
)
from app.services.customer_management_service import (
    create_customer,
    get_customer,
    get_customer_detail,
    list_customers,
    serialise_customer_summary,
    update_customer,
    update_customer_status,
)


router = APIRouter(
    prefix="/customers",
    tags=["Customers"],
)

StaffUser = Annotated[
    User,
    Depends(require_staff_or_admin),
]


def basic_customer_response(customer) -> dict:
    """Return a newly created or updated customer."""

    return serialise_customer_summary(
        customer=customer,
        reservation_count=0,
        order_count=0,
        completed_order_count=0,
        total_paid_spending=0,
    )


@router.get("")
def read_customers(
    database: DatabaseSession,
    current_user: StaffUser,
    search: str | None = Query(
        default=None,
        max_length=120,
    ),
    include_inactive: bool = Query(default=True),
):
    """Return searchable customers."""

    del current_user

    customers = list_customers(
        database=database,
        search=search,
        include_inactive=include_inactive,
    )

    response_data = [
        CustomerSummaryResponse.model_validate(
            customer
        ).model_dump(mode="json")
        for customer in customers
    ]

    return success_response(
        message="Customers retrieved successfully.",
        data=response_data,
    )


@router.post("", status_code=201)
def add_customer(
    customer_data: CustomerCreate,
    database: DatabaseSession,
    current_user: StaffUser,
):
    """Create a customer record."""

    del current_user

    customer = create_customer(
        database=database,
        customer_data=customer_data,
    )

    response_data = CustomerSummaryResponse.model_validate(
        basic_customer_response(customer)
    )

    return success_response(
        message="Customer created successfully.",
        data=response_data.model_dump(mode="json"),
        status_code=201,
    )


@router.get("/{customer_id}")
def read_customer(
    customer_id: int,
    database: DatabaseSession,
    current_user: StaffUser,
):
    """Return customer details and activity."""

    del current_user

    customer_data = get_customer_detail(
        database=database,
        customer_id=customer_id,
    )

    response_data = CustomerDetailResponse.model_validate(
        customer_data
    )

    return success_response(
        message="Customer retrieved successfully.",
        data=response_data.model_dump(mode="json"),
    )


@router.put("/{customer_id}")
def edit_customer(
    customer_id: int,
    customer_data: CustomerUpdate,
    database: DatabaseSession,
    current_user: StaffUser,
):
    """Update customer information."""

    del current_user

    customer = get_customer(database, customer_id)

    updated_customer = update_customer(
        database=database,
        customer=customer,
        customer_data=customer_data,
    )

    response_data = CustomerSummaryResponse.model_validate(
        basic_customer_response(updated_customer)
    )

    return success_response(
        message="Customer updated successfully.",
        data=response_data.model_dump(mode="json"),
    )


@router.patch("/{customer_id}/status")
def change_customer_status(
    customer_id: int,
    status_data: CustomerStatusUpdate,
    database: DatabaseSession,
    current_user: StaffUser,
):
    """Activate or deactivate a customer."""

    del current_user

    customer = get_customer(database, customer_id)

    updated_customer = update_customer_status(
        database=database,
        customer=customer,
        is_active=status_data.is_active,
    )

    response_data = CustomerSummaryResponse.model_validate(
        basic_customer_response(updated_customer)
    )

    return success_response(
        message="Customer status updated successfully.",
        data=response_data.model_dump(mode="json"),
    )