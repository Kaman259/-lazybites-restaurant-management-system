"""Restaurant order model."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Index,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin
from app.utils.enums import (
    OrderStatus,
    OrderType,
    enum_values,
)

if TYPE_CHECKING:
    from app.models.customer import Customer
    from app.models.dining_table import DiningTable
    from app.models.invoice import Invoice
    from app.models.order_item import OrderItem
    from app.models.reservation import Reservation
    from app.models.user import User


class Order(TimestampMixin, Base):
    """A dine-in, takeaway, or delivery food order."""

    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True)

    order_number: Mapped[str] = mapped_column(
        String(30),
        unique=True,
        nullable=False,
    )

    customer_id: Mapped[int | None] = mapped_column(
        ForeignKey(
            "customers.id",
            ondelete="SET NULL",
        ),
        nullable=True,
    )

    table_id: Mapped[int | None] = mapped_column(
        ForeignKey(
            "dining_tables.id",
            ondelete="RESTRICT",
        ),
        nullable=True,
    )

    reservation_id: Mapped[int | None] = mapped_column(
        ForeignKey(
            "reservations.id",
            ondelete="SET NULL",
        ),
        nullable=True,
    )

    invoice_id: Mapped[int | None] = mapped_column(
        ForeignKey(
            "invoices.id",
            ondelete="RESTRICT",
        ),
        nullable=True,
    )

    created_by_user_id: Mapped[int] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )

    order_type: Mapped[OrderType] = mapped_column(
        SAEnum(
            OrderType,
            values_callable=enum_values,
            native_enum=False,
            create_constraint=False,
            validate_strings=True,
            length=20,
        ),
        nullable=False,
    )

    status: Mapped[OrderStatus] = mapped_column(
        SAEnum(
            OrderStatus,
            values_callable=enum_values,
            native_enum=False,
            create_constraint=False,
            validate_strings=True,
            length=20,
        ),
        default=OrderStatus.PENDING,
        nullable=False,
    )

    special_instructions: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    delivery_address: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    cancelled_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    cancellation_reason: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    customer: Mapped[Customer | None] = relationship(
        "Customer",
        back_populates="orders",
    )

    table: Mapped[DiningTable | None] = relationship(
        "DiningTable",
        back_populates="orders",
    )

    reservation: Mapped[Reservation | None] = relationship(
        "Reservation",
        back_populates="orders",
    )

    invoice: Mapped[Invoice | None] = relationship(
        "Invoice",
        back_populates="orders",
    )

    created_by: Mapped[User] = relationship(
        "User",
        back_populates="created_orders",
        foreign_keys=[created_by_user_id],
    )

    items: Mapped[list[OrderItem]] = relationship(
        "OrderItem",
        back_populates="order",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("ix_orders_customer_id", "customer_id"),
        Index("ix_orders_table_id", "table_id"),
        Index(
            "ix_orders_reservation_id",
            "reservation_id",
        ),
        Index(
            "ix_orders_invoice_id",
            "invoice_id",
        ),
        Index(
            "ix_orders_created_by_user_id",
            "created_by_user_id",
        ),
        Index("ix_orders_order_type", "order_type"),
        Index("ix_orders_status", "status"),
        Index("ix_orders_created_at", "created_at"),
        Index(
            "ix_orders_table_status",
            "table_id",
            "status",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"Order(id={self.id!r}, "
            f"order_number={self.order_number!r})"
        )