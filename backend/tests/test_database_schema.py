"""Tests for the initial database schema."""

from sqlalchemy import inspect

from app.database.base import Base
from app.database.session import engine

import app.models  # noqa: F401


EXPECTED_TABLES = {
    "users",
    "restaurant_settings",
    "dining_tables",
    "customers",
    "reservations",
    "menu_categories",
    "menu_items",
    "orders",
    "order_items",
    "invoices",
}


def test_model_metadata_contains_all_tables() -> None:
    """Confirm every approved model is registered."""

    assert set(Base.metadata.tables.keys()) == EXPECTED_TABLES


def test_database_contains_all_tables() -> None:
    """Confirm the Alembic migration created every table."""

    inspector = inspect(engine)
    database_tables = set(inspector.get_table_names())

    assert EXPECTED_TABLES.issubset(database_tables)


def test_foreign_keys_are_enabled_for_sqlite() -> None:
    """Confirm SQLite checks foreign-key constraints."""

    if engine.dialect.name != "sqlite":
        return

    with engine.connect() as connection:
        foreign_keys_enabled = connection.exec_driver_sql(
            "PRAGMA foreign_keys"
        ).scalar_one()

    assert foreign_keys_enabled == 1