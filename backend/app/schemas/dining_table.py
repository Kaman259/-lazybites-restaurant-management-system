"""Schemas for restaurant dining tables."""

from pydantic import BaseModel, ConfigDict, Field, field_validator


class DiningTableCreate(BaseModel):
    """Information required to create a dining table."""

    table_number: str = Field(min_length=1, max_length=20)
    capacity: int = Field(ge=1, le=100)
    area: str = Field(min_length=2, max_length=80)
    description: str | None = Field(default=None, max_length=255)
    is_active: bool = True

    @field_validator("table_number", "area")
    @classmethod
    def clean_required_text(cls, value: str) -> str:
        cleaned_value = value.strip()

        if not cleaned_value:
            raise ValueError("This field cannot be empty.")

        return cleaned_value

    @field_validator("description")
    @classmethod
    def clean_optional_text(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        cleaned_value = value.strip()
        return cleaned_value or None


class DiningTableUpdate(DiningTableCreate):
    """Information used to update a dining table."""


class DiningTableResponse(BaseModel):
    """Dining table returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    table_number: str
    capacity: int
    area: str
    description: str | None
    is_active: bool


class AvailableTableResponse(DiningTableResponse):
    """Dining table available for a selected period."""

    pass