"""Allow multiple orders for one reservation.

Revision ID: 20260727_0002
Revises: 20260721_0001
Create Date: 2026-07-27
"""

from typing import Sequence, Union

from alembic import op


revision: str = "20260727_0002"

down_revision: Union[
    str,
    Sequence[str],
    None,
] = "20260721_0001"

branch_labels: Union[
    str,
    Sequence[str],
    None,
] = None

depends_on: Union[
    str,
    Sequence[str],
    None,
] = None


def disable_sqlite_foreign_keys() -> None:
    """Temporarily disable SQLite foreign-key checks."""

    connection = op.get_bind()

    if connection.dialect.name != "sqlite":
        return

    with op.get_context().autocommit_block():
        connection.exec_driver_sql(
            "PRAGMA foreign_keys=OFF"
        )

        connection.exec_driver_sql(
            "DROP TABLE IF EXISTS _alembic_tmp_orders"
        )


def enable_sqlite_foreign_keys() -> None:
    """Restore SQLite foreign-key checks."""

    connection = op.get_bind()

    if connection.dialect.name != "sqlite":
        return

    with op.get_context().autocommit_block():
        connection.exec_driver_sql(
            "PRAGMA foreign_keys=ON"
        )


def upgrade() -> None:
    """Remove the one-order-per-reservation restriction."""

    disable_sqlite_foreign_keys()

    try:
        with op.batch_alter_table(
            "orders",
            recreate="always",
        ) as batch_operation:
            batch_operation.drop_constraint(
                "uq_orders_reservation_id",
                type_="unique",
            )

            batch_operation.create_index(
                "ix_orders_reservation_id",
                ["reservation_id"],
                unique=False,
            )
    finally:
        enable_sqlite_foreign_keys()


def downgrade() -> None:
    """Restore the one-order-per-reservation restriction."""

    disable_sqlite_foreign_keys()

    try:
        with op.batch_alter_table(
            "orders",
            recreate="always",
        ) as batch_operation:
            batch_operation.drop_index(
                "ix_orders_reservation_id"
            )

            batch_operation.create_unique_constraint(
                "uq_orders_reservation_id",
                ["reservation_id"],
            )
    finally:
        enable_sqlite_foreign_keys()