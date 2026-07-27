"""Restaurant settings service functions."""

from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.restaurant_settings import RestaurantSettings
from app.schemas.restaurant_settings import RestaurantSettingsUpdate


def get_restaurant_settings(
    database: Session,
) -> RestaurantSettings:
    """Return the single settings record, creating it when absent."""

    statement = select(RestaurantSettings).limit(1)
    settings_record = database.scalar(statement)

    if settings_record is not None:
        return settings_record

    settings_record = RestaurantSettings(
        restaurant_name="LazyBites Restaurant",
        address="Jorhat, Assam",
        phone="0000000000",
        email=None,
        gstin=None,
        default_gst_percentage=Decimal("5.00"),
        currency="INR",
        invoice_prefix="INV",
        receipt_footer="Thank you for dining with us.",
        logo_path=None,
        timezone="Asia/Kolkata",
    )

    database.add(settings_record)
    database.commit()
    database.refresh(settings_record)

    return settings_record


def update_restaurant_settings(
    database: Session,
    settings_record: RestaurantSettings,
    update_data: RestaurantSettingsUpdate,
) -> RestaurantSettings:
    """Update the restaurant configuration."""

    update_values = update_data.model_dump()

    for field_name, field_value in update_values.items():
        setattr(settings_record, field_name, field_value)

    database.add(settings_record)
    database.commit()
    database.refresh(settings_record)

    return settings_record


def update_restaurant_logo(
    database: Session,
    settings_record: RestaurantSettings,
    logo_path: str,
) -> RestaurantSettings:
    """Save the public restaurant logo path."""

    settings_record.logo_path = logo_path

    database.add(settings_record)
    database.commit()
    database.refresh(settings_record)

    return settings_record