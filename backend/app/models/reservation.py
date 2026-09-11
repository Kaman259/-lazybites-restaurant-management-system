"""Table reservation model."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Index,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin
from app.utils.enums import ReservationStatus, enum_values

if TYPE_CHECKING:
    from app.models.customer import Customer
    from app.models.dining_table import DiningTable
    from app.models.order import Order
    from app.models.user import User


class Reservation(TimestampMixin, Base):
    """A dining table reservation for a customer."""

    __tablename__ = "reservations"

    id: Mapped[int] = mapped_column(primary_key=True)

    reservation_number: Mapped[str] = mapped_column(
        String(30),
        unique=True,
        nullable=False,
    )

    customer_id: Mapped[int] = mapped_column(
        ForeignKey(
            "customers.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )

    table_id: Mapped[int] = mapped_column(
        ForeignKey(
            "dining_tables.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )

    created_by_user_id: Mapped[int] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )

    start_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    end_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    guest_count: Mapped[int] = mapped_column(
        nullable=False,
    )

    status: Mapped[ReservationStatus] = mapped_column(
        SAEnum(
            ReservationStatus,
            values_callable=enum_values,
            native_enum=False,
            create_constraint=False,
            validate_strings=True,
            length=20,
        ),
        default=ReservationStatus.PENDING,
        nullable=False,
    )

    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    cancellation_reason: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    cancelled_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    customer: Mapped[Customer] = relationship(
        "Customer",
        back_populates="reservations",
    )

    table: Mapped[DiningTable] = relationship(
        "DiningTable",
        back_populates="reservations",
    )

    created_by: Mapped[User] = relationship(
        "User",
        back_populates="created_reservations",
        foreign_keys=[created_by_user_id],
    )

    orders: Mapped[list[Order]] = relationship(
        "Order",
        back_populates="reservation",
    )

    __table_args__ = (
        CheckConstraint(
            "guest_count > 0",
            name="guest_count_positive",
        ),
        CheckConstraint(
            "end_time > start_time",
            name="end_time_after_start_time",
        ),
        Index(
            "ix_reservations_customer_id",
            "customer_id",
        ),
        Index(
            "ix_reservations_table_id",
            "table_id",
        ),
        Index(
            "ix_reservations_status",
            "status",
        ),
        Index(
            "ix_reservations_start_time",
            "start_time",
        ),
        Index(
            "ix_reservations_end_time",
            "end_time",
        ),
        Index(
            "ix_reservations_table_time",
            "table_id",
            "start_time",
            "end_time",
        ),
        Index(
            "ix_reservations_customer_start",
            "customer_id",
            "start_time",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"Reservation(id={self.id!r}, "
            f"reservation_number={self.reservation_number!r})"
        )