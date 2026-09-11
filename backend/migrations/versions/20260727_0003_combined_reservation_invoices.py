"""Allow one invoice to contain multiple orders.

Revision ID: 20260727_0003
Revises: 20260727_0002
Create Date: 2026-07-27
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260727_0003"

down_revision: Union[
    str,
    Sequence[str],
    None,
] = "20260727_0002"

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
    """Temporarily disable SQLite FK checks."""

    connection = op.get_bind()

    if connection.dialect.name != "sqlite":
        return

    with op.get_context().autocommit_block():
        connection.exec_driver_sql(
            "PRAGMA foreign_keys=OFF"
        )

        connection.exec_driver_sql(
            "DROP TABLE IF EXISTS "
            "_alembic_tmp_orders"
        )

        connection.exec_driver_sql(
            "DROP TABLE IF EXISTS "
            "_alembic_tmp_invoices"
        )


def enable_sqlite_foreign_keys() -> None:
    """Restore SQLite FK checks."""

    connection = op.get_bind()

    if connection.dialect.name != "sqlite":
        return

    with op.get_context().autocommit_block():
        connection.exec_driver_sql(
            "PRAGMA foreign_keys=ON"
        )


def upgrade() -> None:
    """
    Move the invoice relationship from invoices.order_id
    to orders.invoice_id while preserving existing data.
    """

    disable_sqlite_foreign_keys()

    try:
        with op.batch_alter_table(
            "orders",
            recreate="always",
        ) as batch_operation:
            batch_operation.add_column(
                sa.Column(
                    "invoice_id",
                    sa.Integer(),
                    nullable=True,
                )
            )

            batch_operation.create_foreign_key(
                "fk_orders_invoice_id_invoices",
                "invoices",
                ["invoice_id"],
                ["id"],
                ondelete="RESTRICT",
            )

            batch_operation.create_index(
                "ix_orders_invoice_id",
                ["invoice_id"],
                unique=False,
            )

        op.execute(
            sa.text(
                """
                UPDATE orders
                SET invoice_id = (
                    SELECT invoices.id
                    FROM invoices
                    WHERE invoices.order_id = orders.id
                )
                WHERE EXISTS (
                    SELECT 1
                    FROM invoices
                    WHERE invoices.order_id = orders.id
                )
                """
            )
        )

        with op.batch_alter_table(
            "invoices",
            recreate="always",
        ) as batch_operation:
            batch_operation.drop_constraint(
                "uq_invoices_order_id",
                type_="unique",
            )

            batch_operation.drop_constraint(
                "fk_invoices_order_id_orders",
                type_="foreignkey",
            )

            batch_operation.drop_column(
                "order_id"
            )

    finally:
        enable_sqlite_foreign_keys()


def downgrade() -> None:
    """
    Restore the previous one-invoice-per-order structure.

    A downgrade is refused if a combined invoice currently
    contains more than one order because that relationship
    cannot be represented by the old schema without losing
    data.
    """

    connection = op.get_bind()

    combined_invoice = connection.execute(
        sa.text(
            """
            SELECT invoice_id
            FROM orders
            WHERE invoice_id IS NOT NULL
            GROUP BY invoice_id
            HAVING COUNT(*) > 1
            LIMIT 1
            """
        )
    ).first()

    if combined_invoice is not None:
        raise RuntimeError(
            "Cannot downgrade while a combined invoice "
            "contains multiple orders."
        )

    disable_sqlite_foreign_keys()

    try:
        with op.batch_alter_table(
            "invoices",
            recreate="always",
        ) as batch_operation:
            batch_operation.add_column(
                sa.Column(
                    "order_id",
                    sa.Integer(),
                    nullable=True,
                )
            )

            batch_operation.create_foreign_key(
                "fk_invoices_order_id_orders",
                "orders",
                ["order_id"],
                ["id"],
                ondelete="RESTRICT",
            )

        op.execute(
            sa.text(
                """
                UPDATE invoices
                SET order_id = (
                    SELECT orders.id
                    FROM orders
                    WHERE orders.invoice_id = invoices.id
                    LIMIT 1
                )
                """
            )
        )

        missing_order = connection.execute(
            sa.text(
                """
                SELECT id
                FROM invoices
                WHERE order_id IS NULL
                LIMIT 1
                """
            )
        ).first()

        if missing_order is not None:
            raise RuntimeError(
                "Cannot downgrade because an invoice "
                "does not have an associated order."
            )

        with op.batch_alter_table(
            "invoices",
            recreate="always",
        ) as batch_operation:
            batch_operation.alter_column(
                "order_id",
                existing_type=sa.Integer(),
                nullable=False,
            )

            batch_operation.create_unique_constraint(
                "uq_invoices_order_id",
                ["order_id"],
            )

        with op.batch_alter_table(
            "orders",
            recreate="always",
        ) as batch_operation:
            batch_operation.drop_index(
                "ix_orders_invoice_id"
            )

            batch_operation.drop_constraint(
                "fk_orders_invoice_id_invoices",
                type_="foreignkey",
            )

            batch_operation.drop_column(
                "invoice_id"
            )

    finally:
        enable_sqlite_foreign_keys()