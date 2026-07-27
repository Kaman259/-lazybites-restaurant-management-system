"""Dining table model."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, CheckConstraint, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.order import Order
    from app.models.reservation import Reservation


class DiningTable(TimestampMixin, Base):
    """A physical dining table inside the restaurant."""

    __tablename__ = "dining_tables"

    id: Mapped[int] = mapped_column(primary_key=True)

    table_number: Mapped[str] = mapped_column(
        String(20),
        unique=True,
        nullable=False,
    )

    capacity: Mapped[int] = mapped_column(
        nullable=False,
    )

    area: Mapped[str] = mapped_column(
        String(80),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    reservations: Mapped[list[Reservation]] = relationship(
        "Reservation",
        back_populates="table",
    )

    orders: Mapped[list[Order]] = relationship(
        "Order",
        back_populates="table",
    )

    __table_args__ = (
        CheckConstraint(
            "capacity > 0",
            name="capacity_positive",
        ),
        Index("ix_dining_tables_area", "area"),
        Index("ix_dining_tables_is_active", "is_active"),
    )

    def __repr__(self) -> str:
        return (
            f"DiningTable(id={self.id!r}, "
            f"table_number={self.table_number!r})"
        )