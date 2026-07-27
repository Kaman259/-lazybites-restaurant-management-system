"""Menu item model."""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Enum as SAEnum,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin
from app.utils.enums import FoodType, enum_values

if TYPE_CHECKING:
    from app.models.menu_category import MenuCategory
    from app.models.order_item import OrderItem


class MenuItem(TimestampMixin, Base):
    """A food or beverage available on the restaurant menu."""

    __tablename__ = "menu_items"

    id: Mapped[int] = mapped_column(primary_key=True)

    category_id: Mapped[int] = mapped_column(
        ForeignKey(
            "menu_categories.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )

    name: Mapped[str] = mapped_column(
        String(120),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    price: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
    )

    food_type: Mapped[FoodType] = mapped_column(
        SAEnum(
            FoodType,
            values_callable=enum_values,
            native_enum=False,
            create_constraint=False,
            validate_strings=True,
            length=20,
        ),
        nullable=False,
    )

    image_path: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    is_available: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    category: Mapped[MenuCategory] = relationship(
        "MenuCategory",
        back_populates="menu_items",
    )

    order_items: Mapped[list[OrderItem]] = relationship(
        "OrderItem",
        back_populates="menu_item",
    )

    __table_args__ = (
        UniqueConstraint(
            "category_id",
            "name",
            name="uq_menu_items_category_name",
        ),
        CheckConstraint(
            "price > 0",
            name="price_positive",
        ),
        Index("ix_menu_items_category_id", "category_id"),
        Index("ix_menu_items_food_type", "food_type"),
        Index("ix_menu_items_is_available", "is_available"),
        Index("ix_menu_items_is_active", "is_active"),
        Index("ix_menu_items_name", "name"),
    )

    def __repr__(self) -> str:
        return (
            f"MenuItem(id={self.id!r}, name={self.name!r}, "
            f"price={self.price!r})"
        )