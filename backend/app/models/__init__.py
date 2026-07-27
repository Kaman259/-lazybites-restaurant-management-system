"""SQLAlchemy model exports.

Importing this package registers every model with SQLAlchemy metadata.
"""

from app.models.customer import Customer
from app.models.dining_table import DiningTable
from app.models.invoice import Invoice
from app.models.menu_category import MenuCategory
from app.models.menu_item import MenuItem
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.reservation import Reservation
from app.models.restaurant_settings import RestaurantSettings
from app.models.user import User

__all__ = [
    "User",
    "RestaurantSettings",
    "DiningTable",
    "Customer",
    "Reservation",
    "MenuCategory",
    "MenuItem",
    "Order",
    "OrderItem",
    "Invoice",
]