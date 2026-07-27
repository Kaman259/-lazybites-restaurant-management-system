"""Schemas for restaurant orders and order items."""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.utils.enums import OrderStatus, OrderType


class OrderItemCreate(BaseModel):
    """One menu item submitted while creating an order."""

    menu_item_id: int = Field(gt=0)
    quantity: int = Field(ge=1, le=100)
    special_instruction: str | None = Field(
        default=None,
        max_length=255,
    )

    @field_validator("special_instruction")
    @classmethod
    def clean_special_instruction(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        cleaned_value = value.strip()
        return cleaned_value or None


class OrderCreate(BaseModel):
    """Information required to create an order."""

    customer_id: int | None = Field(default=None, gt=0)
    table_id: int | None = Field(default=None, gt=0)
    reservation_id: int | None = Field(default=None, gt=0)

    order_type: OrderType

    special_instructions: str | None = None
    delivery_address: str | None = None

    items: list[OrderItemCreate] = Field(
        min_length=1,
        max_length=100,
    )

    @field_validator(
        "special_instructions",
        "delivery_address",
    )
    @classmethod
    def clean_optional_text(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        cleaned_value = value.strip()
        return cleaned_value or None


class OrderStatusUpdate(BaseModel):
    """Order status update submitted by Staff or Admin."""

    status: OrderStatus

    cancellation_reason: str | None = Field(
        default=None,
        max_length=255,
    )

    @field_validator("cancellation_reason")
    @classmethod
    def clean_cancellation_reason(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        cleaned_value = value.strip()
        return cleaned_value or None


class OrderItemResponse(BaseModel):
    """Order item returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    menu_item_id: int
    item_name: str
    unit_price: Decimal
    quantity: int
    special_instruction: str | None
    line_total: Decimal
    created_at: datetime


class OrderCustomerResponse(BaseModel):
    """Small customer summary included with an order."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    full_name: str
    phone: str
    email: str | None


class OrderTableResponse(BaseModel):
    """Small dining-table summary included with an order."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    table_number: str
    capacity: int
    area: str


class OrderReservationResponse(BaseModel):
    """Small reservation summary included with an order."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    reservation_number: str


class OrderResponse(BaseModel):
    """Complete order returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    order_number: str

    customer_id: int | None
    table_id: int | None
    reservation_id: int | None
    created_by_user_id: int

    order_type: OrderType
    status: OrderStatus

    special_instructions: str | None
    delivery_address: str | None

    completed_at: datetime | None
    cancelled_at: datetime | None
    cancellation_reason: str | None

    created_at: datetime
    updated_at: datetime

    items: list[OrderItemResponse]
    customer: OrderCustomerResponse | None
    table: OrderTableResponse | None
    reservation: OrderReservationResponse | None

    subtotal: Decimal