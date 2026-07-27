"""Customer model."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.order import Order
    from app.models.reservation import Reservation
    from app.models.user import User


class Customer(TimestampMixin, Base):
    """Registered or staff-created restaurant customer."""

    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(primary_key=True)

    user_id: Mapped[int | None] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="SET NULL",
        ),
        unique=True,
        nullable=True,
    )

    full_name: Mapped[str] = mapped_column(
        String(120),
        nullable=False,
    )

    phone: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    email: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    address: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    user: Mapped[User | None] = relationship(
        "User",
        back_populates="customer_profile",
    )

    reservations: Mapped[list[Reservation]] = relationship(
        "Reservation",
        back_populates="customer",
    )

    orders: Mapped[list[Order]] = relationship(
        "Order",
        back_populates="customer",
    )

    __table_args__ = (
        Index("ix_customers_phone", "phone"),
        Index("ix_customers_email", "email"),
        Index("ix_customers_is_active", "is_active"),
    )

    def __repr__(self) -> str:
        return (
            f"Customer(id={self.id!r}, "
            f"full_name={self.full_name!r})"
        )