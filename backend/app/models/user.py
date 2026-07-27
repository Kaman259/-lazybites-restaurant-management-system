"""Application user model linked to Firebase Authentication."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Enum as SAEnum, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin
from app.utils.enums import UserRole, enum_values

if TYPE_CHECKING:
    from app.models.customer import Customer
    from app.models.order import Order
    from app.models.reservation import Reservation


class User(TimestampMixin, Base):
    """Local application record for a Firebase user."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)

    firebase_uid: Mapped[str] = mapped_column(
        String(128),
        unique=True,
        nullable=False,
    )

    full_name: Mapped[str] = mapped_column(
        String(120),
        nullable=False,
    )

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
    )

    role: Mapped[UserRole] = mapped_column(
        SAEnum(
            UserRole,
            values_callable=enum_values,
            native_enum=False,
            create_constraint=False,
            validate_strings=True,
            length=20,
        ),
        nullable=False,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    last_login_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    customer_profile: Mapped[Customer | None] = relationship(
        "Customer",
        back_populates="user",
        uselist=False,
    )

    created_reservations: Mapped[list[Reservation]] = relationship(
        "Reservation",
        back_populates="created_by",
        foreign_keys="Reservation.created_by_user_id",
    )

    created_orders: Mapped[list[Order]] = relationship(
        "Order",
        back_populates="created_by",
        foreign_keys="Order.created_by_user_id",
    )

    __table_args__ = (
        Index("ix_users_role", "role"),
        Index("ix_users_is_active", "is_active"),
    )

    def __repr__(self) -> str:
        return (
            f"User(id={self.id!r}, email={self.email!r}, "
            f"role={self.role!r})"
        )