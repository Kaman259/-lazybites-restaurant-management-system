"""Schemas for invoices, payments, and refunds."""

from datetime import datetime
from decimal import Decimal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
)

from app.utils.enums import (
    DiscountType,
    OrderType,
    PaymentMethod,
    PaymentStatus,
)


class InvoiceCreate(BaseModel):
    """Information required to generate an invoice."""

    order_id: int = Field(gt=0)

    discount_type: DiscountType = DiscountType.NONE

    discount_value: Decimal = Field(
        default=Decimal("0.00"),
        ge=Decimal("0.00"),
        max_digits=10,
        decimal_places=2,
    )


class InvoicePaymentUpdate(BaseModel):
    """Payment information submitted for an invoice."""

    payment_method: PaymentMethod


class InvoiceRefundUpdate(BaseModel):
    """Information required to refund a paid invoice."""

    refund_reason: str = Field(
        min_length=1,
        max_length=255,
    )

    @field_validator("refund_reason")
    @classmethod
    def clean_refund_reason(
        cls,
        value: str,
    ) -> str:
        cleaned_value = value.strip()

        if not cleaned_value:
            raise ValueError(
                "Refund reason is required."
            )

        return cleaned_value


class InvoiceOrderItemResponse(BaseModel):
    """Stored order item displayed on an invoice."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    item_name: str
    unit_price: Decimal
    quantity: int
    special_instruction: str | None
    line_total: Decimal


class InvoiceCustomerResponse(BaseModel):
    """Customer information displayed on an invoice."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    full_name: str
    phone: str
    email: str | None


class InvoiceTableResponse(BaseModel):
    """Dining-table information displayed on an invoice."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    table_number: str
    area: str


class InvoiceOrderResponse(BaseModel):
    """Order information included in an invoice response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    order_number: str
    reservation_id: int | None
    order_type: OrderType

    customer: InvoiceCustomerResponse | None
    table: InvoiceTableResponse | None

    items: list[InvoiceOrderItemResponse]

    created_at: datetime


class InvoiceResponse(BaseModel):
    """Complete invoice returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: int

    # Kept temporarily so existing frontend/tests that read
    # invoice.order_id and invoice.order continue to work.
    order_id: int
    order: InvoiceOrderResponse

    orders: list[InvoiceOrderResponse]

    invoice_number: str

    subtotal: Decimal

    discount_type: DiscountType
    discount_value: Decimal
    discount_amount: Decimal

    gst_percentage: Decimal
    gst_amount: Decimal
    grand_total: Decimal

    payment_method: PaymentMethod | None
    payment_status: PaymentStatus

    paid_at: datetime | None
    refunded_at: datetime | None
    refund_reason: str | None

    created_at: datetime
    updated_at: datetime