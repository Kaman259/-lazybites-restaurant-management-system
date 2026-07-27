"""Restaurant configuration model."""

from decimal import Decimal

from sqlalchemy import CheckConstraint, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, TimestampMixin


class RestaurantSettings(TimestampMixin, Base):
    """Configuration values used by the single restaurant."""

    __tablename__ = "restaurant_settings"

    id: Mapped[int] = mapped_column(primary_key=True)

    restaurant_name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    address: Mapped[str] = mapped_column(
        Text,
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

    gstin: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
    )

    default_gst_percentage: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        default=Decimal("5.00"),
        nullable=False,
    )

    currency: Mapped[str] = mapped_column(
        String(10),
        default="INR",
        nullable=False,
    )

    invoice_prefix: Mapped[str] = mapped_column(
        String(10),
        default="INV",
        nullable=False,
    )

    receipt_footer: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    logo_path: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    timezone: Mapped[str] = mapped_column(
        String(50),
        default="Asia/Kolkata",
        nullable=False,
    )

    __table_args__ = (
        CheckConstraint(
            "default_gst_percentage >= 0",
            name="default_gst_percentage_non_negative",
        ),
    )

    def __repr__(self) -> str:
        return (
            "RestaurantSettings("
            f"id={self.id!r}, restaurant_name={self.restaurant_name!r})"
        )