"""Authentication request and response schemas."""

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.utils.enums import UserRole


class FirebaseIdentity(BaseModel):
    """Verified identity obtained from a Firebase ID token."""

    firebase_uid: str
    email: str
    email_verified: bool = False


class CustomerRegistrationRequest(BaseModel):
    """Additional customer information saved after Firebase registration."""

    full_name: str = Field(min_length=2, max_length=120)
    phone: str = Field(min_length=7, max_length=20)
    address: str | None = Field(default=None, max_length=500)

    @field_validator("full_name", "phone")
    @classmethod
    def clean_required_text(cls, value: str) -> str:
        """Remove unnecessary outer whitespace."""

        cleaned_value = value.strip()

        if not cleaned_value:
            raise ValueError("This field cannot be empty.")

        return cleaned_value

    @field_validator("address")
    @classmethod
    def clean_optional_address(
        cls,
        value: str | None,
    ) -> str | None:
        """Normalise an optional customer address."""

        if value is None:
            return None

        cleaned_value = value.strip()
        return cleaned_value or None


class AuthUserResponse(BaseModel):
    """Authenticated local application user."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    firebase_uid: str
    full_name: str
    email: str
    role: UserRole
    is_active: bool


class CustomerProfileSummary(BaseModel):
    """Customer details returned with authentication data."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    full_name: str
    phone: str
    email: str | None
    address: str | None
    is_active: bool


class AuthSessionResponse(BaseModel):
    """Combined authenticated user and customer profile."""

    user: AuthUserResponse
    customer: CustomerProfileSummary | None