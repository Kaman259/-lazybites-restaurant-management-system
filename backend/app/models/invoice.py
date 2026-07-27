"""Invoice and payment model."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Index,
    Numeric,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin
from app.utils.enums import (
    DiscountType,
    PaymentMethod,
    PaymentStatus,
    enum_values,
)

if TYPE_CHECKING:
    from app.models.order import Order


class Invoice(TimestampMixin, Base):
    """Final billing information for an order."""

    __tablename__ = "invoices"

    id: Mapped[int] = mapped_column(primary_key=True)

    order_id: Mapped[int] = mapped_column(
        ForeignKey(
            "orders.id",
            ondelete="RESTRICT",
        ),
        unique=True,
        nullable=False,
    )

    invoice_number: Mapped[str] = mapped_column(
        String(30),
        unique=True,
        nullable=False,
    )

    subtotal: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
    )

    discount_type: Mapped[DiscountType] = mapped_column(
        SAEnum(
            DiscountType,
            values_callable=enum_values,
            native_enum=False,
            create_constraint=False,
            validate_strings=True,
            length=20,
        ),
        default=DiscountType.NONE,
        nullable=False,
    )

    discount_value: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        default=Decimal("0.00"),
        nullable=False,
    )

    discount_amount: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        default=Decimal("0.00"),
        nullable=False,
    )

    gst_percentage: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
    )

    gst_amount: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
    )

    grand_total: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
    )

    payment_method: Mapped[PaymentMethod | None] = mapped_column(
        SAEnum(
            PaymentMethod,
            values_callable=enum_values,
            native_enum=False,
            create_constraint=False,
            validate_strings=True,
            length=20,
        ),
        nullable=True,
    )

    payment_status: Mapped[PaymentStatus] = mapped_column(
        SAEnum(
            PaymentStatus,
            values_callable=enum_values,
            native_enum=False,
            create_constraint=False,
            validate_strings=True,
            length=20,
        ),
        default=PaymentStatus.UNPAID,
        nullable=False,
    )

    paid_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    refunded_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    refund_reason: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    order: Mapped[Order] = relationship(
        "Order",
        back_populates="invoice",
    )

    __table_args__ = (
        CheckConstraint(
            "subtotal >= 0",
            name="subtotal_non_negative",
        ),
        CheckConstraint(
            "discount_value >= 0",
            name="discount_value_non_negative",
        ),
        CheckConstraint(
            "discount_amount >= 0",
            name="discount_amount_non_negative",
        ),
        CheckConstraint(
            "gst_percentage >= 0",
            name="gst_percentage_non_negative",
        ),
        CheckConstraint(
            "gst_amount >= 0",
            name="gst_amount_non_negative",
        ),
        CheckConstraint(
            "grand_total >= 0",
            name="grand_total_non_negative",
        ),
        Index("ix_invoices_payment_status", "payment_status"),
        Index("ix_invoices_payment_method", "payment_method"),
        Index("ix_invoices_paid_at", "paid_at"),
        Index("ix_invoices_created_at", "created_at"),
    )

    def __repr__(self) -> str:
        return (
            f"Invoice(id={self.id!r}, "
            f"invoice_number={self.invoice_number!r})"
        )