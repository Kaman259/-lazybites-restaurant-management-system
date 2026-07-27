"""Schemas for staff-managed customer records."""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.utils.enums import (
    OrderStatus,
    OrderType,
    PaymentStatus,
    ReservationStatus,
)


class CustomerCreate(BaseModel):
    """Information required to create a customer."""

    full_name: str = Field(min_length=1, max_length=120)
    phone: str = Field(min_length=5, max_length=20)
    email: EmailStr | None = None
    address: str | None = None
    notes: str | None = None
    is_active: bool = True

    @field_validator("full_name", "phone")
    @classmethod
    def clean_required_text(cls, value: str) -> str:
        cleaned_value = value.strip()

        if not cleaned_value:
            raise ValueError("This field cannot be empty.")

        return cleaned_value

    @field_validator("address", "notes")
    @classmethod
    def clean_optional_text(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        cleaned_value = value.strip()
        return cleaned_value or None


class CustomerUpdate(CustomerCreate):
    """Information used to update a customer."""


class CustomerStatusUpdate(BaseModel):
    """Customer active status update."""

    is_active: bool


class CustomerSummaryResponse(BaseModel):
    """Customer information shown in the customer list."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int | None
    full_name: str
    phone: str
    email: str | None
    address: str | None
    notes: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    reservation_count: int
    order_count: int
    completed_order_count: int
    total_paid_spending: Decimal


class CustomerReservationResponse(BaseModel):
    """Reservation shown in customer activity."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    reservation_number: str
    start_time: datetime
    end_time: datetime
    guest_count: int
    status: ReservationStatus
    table_number: str


class CustomerOrderResponse(BaseModel):
    """Order shown in customer activity."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    order_number: str
    order_type: OrderType
    status: OrderStatus
    created_at: datetime
    invoice_number: str | None
    payment_status: PaymentStatus | None
    grand_total: Decimal | None


class CustomerDetailResponse(CustomerSummaryResponse):
    """Complete customer record with recent activity."""

    reservations: list[CustomerReservationResponse]
    orders: list[CustomerOrderResponse]