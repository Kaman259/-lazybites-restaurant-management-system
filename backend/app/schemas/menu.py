"""Schemas for menu categories and menu items."""

from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.utils.enums import FoodType


class MenuCategoryCreate(BaseModel):
    """Information required to create a menu category."""

    name: str = Field(min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=255)
    display_order: int = Field(default=0, ge=0)
    is_active: bool = True

    @field_validator("name")
    @classmethod
    def clean_name(cls, value: str) -> str:
        cleaned_value = value.strip()

        if not cleaned_value:
            raise ValueError("Category name cannot be empty.")

        return cleaned_value

    @field_validator("description")
    @classmethod
    def clean_description(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        cleaned_value = value.strip()
        return cleaned_value or None


class MenuCategoryUpdate(MenuCategoryCreate):
    """Information used to update a menu category."""


class MenuCategoryResponse(BaseModel):
    """Menu category returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None
    display_order: int
    is_active: bool


class MenuItemCreate(BaseModel):
    """Information required to create a menu item."""

    category_id: int = Field(gt=0)
    name: str = Field(min_length=1, max_length=120)
    description: str | None = None
    price: Decimal = Field(
        gt=Decimal("0.00"),
        max_digits=10,
        decimal_places=2,
    )
    food_type: FoodType
    is_available: bool = True
    is_active: bool = True

    @field_validator("name")
    @classmethod
    def clean_name(cls, value: str) -> str:
        cleaned_value = value.strip()

        if not cleaned_value:
            raise ValueError("Menu item name cannot be empty.")

        return cleaned_value

    @field_validator("description")
    @classmethod
    def clean_description(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        cleaned_value = value.strip()
        return cleaned_value or None


class MenuItemUpdate(MenuItemCreate):
    """Information used to update a menu item."""


class MenuItemAvailabilityUpdate(BaseModel):
    """Availability value updated by restaurant staff."""

    is_available: bool


class MenuItemResponse(BaseModel):
    """Menu item returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    category_id: int
    name: str
    description: str | None
    price: Decimal
    food_type: FoodType
    image_path: str | None
    is_available: bool
    is_active: bool
    category: MenuCategoryResponse