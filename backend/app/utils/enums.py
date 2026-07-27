"""Enumerations shared across database models and API schemas."""

from enum import Enum
from typing import TypeVar


EnumType = TypeVar("EnumType", bound=Enum)


def enum_values(enum_class: type[EnumType]) -> list[str]:
    """Return the stored string values of an enum class."""

    return [member.value for member in enum_class]


class UserRole(str, Enum):
    """Application user roles."""

    ADMIN = "ADMIN"
    STAFF = "STAFF"
    CUSTOMER = "CUSTOMER"


class ReservationStatus(str, Enum):
    """Reservation lifecycle states."""

    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    SEATED = "SEATED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    NO_SHOW = "NO_SHOW"


class FoodType(str, Enum):
    """Supported food classifications."""

    VEG = "VEG"
    NON_VEG = "NON_VEG"


class OrderType(str, Enum):
    """Supported restaurant order types."""

    DINE_IN = "DINE_IN"
    TAKEAWAY = "TAKEAWAY"
    DELIVERY = "DELIVERY"


class OrderStatus(str, Enum):
    """Order lifecycle states."""

    PENDING = "PENDING"
    PREPARING = "PREPARING"
    READY = "READY"
    SERVED = "SERVED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class DiscountType(str, Enum):
    """Supported invoice discount types."""

    NONE = "NONE"
    PERCENTAGE = "PERCENTAGE"
    FIXED = "FIXED"


class PaymentMethod(str, Enum):
    """Supported payment methods."""

    CASH = "CASH"
    UPI = "UPI"
    CARD = "CARD"


class PaymentStatus(str, Enum):
    """Invoice payment states."""

    UNPAID = "UNPAID"
    PAID = "PAID"
    REFUNDED = "REFUNDED"