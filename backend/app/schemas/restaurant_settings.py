"""Schemas for restaurant settings."""

from decimal import Decimal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class RestaurantSettingsUpdate(BaseModel):
    """Fields that an Admin can update."""

    restaurant_name: str = Field(min_length=2, max_length=150)
    address: str = Field(min_length=5, max_length=1000)
    phone: str = Field(min_length=7, max_length=20)
    email: EmailStr | None = None
    gstin: str | None = Field(default=None, max_length=30)

    default_gst_percentage: Decimal = Field(
        ge=Decimal("0.00"),
        le=Decimal("100.00"),
    )

    currency: str = Field(min_length=2, max_length=10)
    invoice_prefix: str = Field(min_length=1, max_length=10)
    receipt_footer: str | None = Field(default=None, max_length=255)
    timezone: str = Field(min_length=2, max_length=50)

    @field_validator(
        "restaurant_name",
        "address",
        "phone",
        "currency",
        "invoice_prefix",
        "timezone",
    )
    @classmethod
    def clean_required_text(cls, value: str) -> str:
        """Remove outer whitespace from required text."""

        cleaned_value = value.strip()

        if not cleaned_value:
            raise ValueError("This field cannot be empty.")

        return cleaned_value

    @field_validator("gstin", "receipt_footer")
    @classmethod
    def clean_optional_text(
        cls,
        value: str | None,
    ) -> str | None:
        """Normalise optional text values."""

        if value is None:
            return None

        cleaned_value = value.strip()
        return cleaned_value or None

    @field_validator("currency", "invoice_prefix")
    @classmethod
    def convert_to_uppercase(cls, value: str) -> str:
        """Store short codes using uppercase text."""

        return value.strip().upper()


class RestaurantSettingsResponse(BaseModel):
    """Restaurant settings returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    restaurant_name: str
    address: str
    phone: str
    email: str | None
    gstin: str | None
    default_gst_percentage: Decimal
    currency: str
    invoice_prefix: str
    receipt_footer: str | None
    logo_path: str | None
    timezone: str