"""Menu category model."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, CheckConstraint, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.menu_item import MenuItem


class MenuCategory(TimestampMixin, Base):
    """A category used to group menu items."""

    __tablename__ = "menu_categories"

    id: Mapped[int] = mapped_column(primary_key=True)

    name: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    display_order: Mapped[int] = mapped_column(
        default=0,
        nullable=False,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    menu_items: Mapped[list[MenuItem]] = relationship(
        "MenuItem",
        back_populates="category",
    )

    __table_args__ = (
        CheckConstraint(
            "display_order >= 0",
            name="display_order_non_negative",
        ),
        Index("ix_menu_categories_is_active", "is_active"),
        Index("ix_menu_categories_display_order", "display_order"),
    )

    def __repr__(self) -> str:
        return (
            f"MenuCategory(id={self.id!r}, name={self.name!r})"
        )