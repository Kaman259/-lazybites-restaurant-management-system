"""Order item model."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, utc_now

if TYPE_CHECKING:
    from app.models.menu_item import MenuItem
    from app.models.order import Order


class OrderItem(Base):
    """A menu item and quantity stored inside an order."""

    __tablename__ = "order_items"

    id: Mapped[int] = mapped_column(primary_key=True)

    order_id: Mapped[int] = mapped_column(
        ForeignKey(
            "orders.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    menu_item_id: Mapped[int] = mapped_column(
        ForeignKey(
            "menu_items.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )

    item_name: Mapped[str] = mapped_column(
        String(120),
        nullable=False,
    )

    unit_price: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
    )

    quantity: Mapped[int] = mapped_column(
        nullable=False,
    )

    special_instruction: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    line_total: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )

    order: Mapped[Order] = relationship(
        "Order",
        back_populates="items",
    )

    menu_item: Mapped[MenuItem] = relationship(
        "MenuItem",
        back_populates="order_items",
    )

    __table_args__ = (
        CheckConstraint(
            "quantity > 0",
            name="quantity_positive",
        ),
        CheckConstraint(
            "unit_price > 0",
            name="unit_price_positive",
        ),
        CheckConstraint(
            "line_total >= 0",
            name="line_total_non_negative",
        ),
        Index("ix_order_items_order_id", "order_id"),
        Index("ix_order_items_menu_item_id", "menu_item_id"),
        Index(
            "ix_order_items_order_menu_item",
            "order_id",
            "menu_item_id",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"OrderItem(id={self.id!r}, "
            f"item_name={self.item_name!r}, "
            f"quantity={self.quantity!r})"
        )