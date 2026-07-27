"""Application user schemas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr

from app.utils.enums import UserRole


class UserResponse(BaseModel):
    """Public application user information."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    firebase_uid: str
    full_name: str
    email: EmailStr
    role: UserRole
    is_active: bool
    last_login_at: datetime | None
    created_at: datetime
    updated_at: datetime