"""Schemas for table reservations."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.dining_table import DiningTableResponse
from app.utils.enums import ReservationStatus


class AvailabilitySearch(BaseModel):
    """Search values used to find free tables."""

    start_time: datetime
    end_time: datetime
    guest_count: int = Field(ge=1, le=100)

    @field_validator("end_time")
    @classmethod
    def validate_time_range(
        cls,
        end_time: datetime,
        validation_info,
    ) -> datetime:
        start_time = validation_info.data.get("start_time")

        if start_time is not None and end_time <= start_time:
            raise ValueError("End time must be after start time.")

        return end_time


class CustomerReservationCreate(AvailabilitySearch):
    """Reservation information submitted by a customer."""

    table_id: int = Field(gt=0)
    notes: str | None = Field(default=None, max_length=1000)

    @field_validator("notes")
    @classmethod
    def clean_notes(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        cleaned_value = value.strip()
        return cleaned_value or None


class ReservationCancelRequest(BaseModel):
    """Reason supplied when cancelling a reservation."""

    cancellation_reason: str | None = Field(
        default=None,
        max_length=255,
    )

    @field_validator("cancellation_reason")
    @classmethod
    def clean_reason(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        cleaned_value = value.strip()
        return cleaned_value or None


class ReservationStatusUpdate(BaseModel):
    """Reservation status changed by Staff or Admin."""

    status: ReservationStatus
    cancellation_reason: str | None = Field(
        default=None,
        max_length=255,
    )

    @field_validator("cancellation_reason")
    @classmethod
    def clean_reason(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        cleaned_value = value.strip()
        return cleaned_value or None


class ReservationCustomerResponse(BaseModel):
    """Small customer summary returned with a reservation."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    full_name: str
    phone: str
    email: str | None


class ReservationResponse(BaseModel):
    """Reservation returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    reservation_number: str
    customer_id: int
    table_id: int
    created_by_user_id: int
    start_time: datetime
    end_time: datetime
    guest_count: int
    status: ReservationStatus
    notes: str | None
    cancellation_reason: str | None
    cancelled_at: datetime | None
    table: DiningTableResponse
    customer: ReservationCustomerResponse