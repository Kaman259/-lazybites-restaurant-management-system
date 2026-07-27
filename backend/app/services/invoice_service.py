"""Invoice calculation and payment service functions."""

from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from secrets import token_hex

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.core.exceptions import AppException
from app.models.invoice import Invoice
from app.models.order import Order
from app.models.restaurant_settings import RestaurantSettings
from app.schemas.invoice import InvoiceCreate
from app.services.settings_service import get_restaurant_settings
from app.utils.enums import (
    DiscountType,
    OrderStatus,
    PaymentMethod,
    PaymentStatus,
)


MONEY_PLACES = Decimal("0.01")


def money(value: Decimal) -> Decimal:
    """Round a monetary value to two decimal places."""

    return Decimal(value).quantize(
        MONEY_PLACES,
        rounding=ROUND_HALF_UP,
    )


def naive_utc_now() -> datetime:
    """Return the current UTC time for existing SQLite columns."""

    return datetime.now(timezone.utc).replace(tzinfo=None)


def invoice_query():
    """Build the standard invoice query."""

    return select(Invoice).options(
        joinedload(Invoice.order).joinedload(Order.items),
        joinedload(Invoice.order).joinedload(Order.customer),
        joinedload(Invoice.order).joinedload(Order.table),
    )


def get_invoice(
    database: Session,
    invoice_id: int,
) -> Invoice:
    """Return one invoice with its order information."""

    statement = invoice_query().where(
        Invoice.id == invoice_id
    )

    result = database.execute(statement)
    invoice = result.unique().scalar_one_or_none()

    if invoice is None:
        raise AppException(
            message="Invoice was not found.",
            status_code=404,
        )

    return invoice


def get_invoice_by_order(
    database: Session,
    order_id: int,
) -> Invoice | None:
    """Return an invoice using its order ID."""

    statement = invoice_query().where(
        Invoice.order_id == order_id
    )

    result = database.execute(statement)

    return result.unique().scalar_one_or_none()


def list_invoices(
    database: Session,
    payment_status: PaymentStatus | None = None,
    payment_method: PaymentMethod | None = None,
) -> list[Invoice]:
    """Return filtered invoices, newest first."""

    statement = invoice_query()

    if payment_status is not None:
        statement = statement.where(
            Invoice.payment_status == payment_status
        )

    if payment_method is not None:
        statement = statement.where(
            Invoice.payment_method == payment_method
        )

    statement = statement.order_by(
        Invoice.created_at.desc()
    )

    result = database.execute(statement)

    return list(result.unique().scalars().all())


def get_completed_order(
    database: Session,
    order_id: int,
) -> Order:
    """Return a completed order that can be invoiced."""

    statement = (
        select(Order)
        .options(
            joinedload(Order.items),
            joinedload(Order.customer),
            joinedload(Order.table),
        )
        .where(Order.id == order_id)
    )

    result = database.execute(statement)
    order = result.unique().scalar_one_or_none()

    if order is None:
        raise AppException(
            message="Order was not found.",
            status_code=404,
        )

    if order.status != OrderStatus.COMPLETED:
        raise AppException(
            message=(
                "Only completed orders can be converted "
                "into invoices."
            ),
            status_code=409,
        )

    if not order.items:
        raise AppException(
            message="The selected order does not contain any items.",
            status_code=409,
        )

    return order


def calculate_subtotal(order: Order) -> Decimal:
    """Calculate subtotal using stored order-item totals."""

    subtotal = sum(
        (
            Decimal(order_item.line_total)
            for order_item in order.items
        ),
        Decimal("0.00"),
    )

    return money(subtotal)


def calculate_discount(
    subtotal: Decimal,
    discount_type: DiscountType,
    discount_value: Decimal,
) -> Decimal:
    """Calculate a valid invoice discount."""

    cleaned_value = money(discount_value)

    if discount_type == DiscountType.NONE:
        if cleaned_value != Decimal("0.00"):
            raise AppException(
                message=(
                    "Discount value must be zero when "
                    "discount type is NONE."
                ),
                status_code=400,
            )

        return Decimal("0.00")

    if discount_type == DiscountType.PERCENTAGE:
        if cleaned_value > Decimal("100.00"):
            raise AppException(
                message=(
                    "Percentage discount cannot be "
                    "greater than 100."
                ),
                status_code=400,
            )

        return money(
            subtotal * cleaned_value / Decimal("100.00")
        )

    if discount_type == DiscountType.FIXED:
        if cleaned_value > subtotal:
            raise AppException(
                message=(
                    "Fixed discount cannot be greater "
                    "than the order subtotal."
                ),
                status_code=400,
            )

        return cleaned_value

    raise AppException(
        message="Unsupported discount type.",
        status_code=400,
    )


def generate_invoice_number(
    database: Session,
    settings_record: RestaurantSettings,
) -> str:
    """Generate a readable unique invoice number."""

    prefix = settings_record.invoice_prefix.strip().upper()
    date_part = datetime.now(timezone.utc).strftime("%Y%m%d")

    for _ in range(10):
        invoice_number = (
            f"{prefix}-{date_part}-{token_hex(2).upper()}"
        )

        existing_id = database.scalar(
            select(Invoice.id).where(
                Invoice.invoice_number == invoice_number
            )
        )

        if existing_id is None:
            return invoice_number

    raise AppException(
        message="An invoice number could not be generated.",
        status_code=500,
    )


def create_invoice(
    database: Session,
    invoice_data: InvoiceCreate,
) -> Invoice:
    """Create an invoice from a completed order."""

    existing_invoice = get_invoice_by_order(
        database=database,
        order_id=invoice_data.order_id,
    )

    if existing_invoice is not None:
        raise AppException(
            message="This order already has an invoice.",
            status_code=409,
        )

    order = get_completed_order(
        database=database,
        order_id=invoice_data.order_id,
    )

    settings_record = get_restaurant_settings(database)

    subtotal = calculate_subtotal(order)

    discount_amount = calculate_discount(
        subtotal=subtotal,
        discount_type=invoice_data.discount_type,
        discount_value=invoice_data.discount_value,
    )

    taxable_amount = money(
        subtotal - discount_amount
    )

    gst_percentage = money(
        Decimal(settings_record.default_gst_percentage)
    )

    gst_amount = money(
        taxable_amount
        * gst_percentage
        / Decimal("100.00")
    )

    grand_total = money(
        taxable_amount + gst_amount
    )

    invoice = Invoice(
        order_id=order.id,
        invoice_number=generate_invoice_number(
            database,
            settings_record,
        ),
        subtotal=subtotal,
        discount_type=invoice_data.discount_type,
        discount_value=money(
            invoice_data.discount_value
        ),
        discount_amount=discount_amount,
        gst_percentage=gst_percentage,
        gst_amount=gst_amount,
        grand_total=grand_total,
        payment_method=None,
        payment_status=PaymentStatus.UNPAID,
        paid_at=None,
        refunded_at=None,
        refund_reason=None,
    )

    database.add(invoice)
    database.commit()

    return get_invoice(database, invoice.id)


def mark_invoice_paid(
    database: Session,
    invoice_id: int,
    payment_method: PaymentMethod,
) -> Invoice:
    """Mark an unpaid invoice as paid."""

    invoice = get_invoice(database, invoice_id)

    if invoice.payment_status == PaymentStatus.PAID:
        raise AppException(
            message="This invoice has already been paid.",
            status_code=409,
        )

    if invoice.payment_status == PaymentStatus.REFUNDED:
        raise AppException(
            message="A refunded invoice cannot be paid again.",
            status_code=409,
        )

    invoice.payment_method = payment_method
    invoice.payment_status = PaymentStatus.PAID
    invoice.paid_at = naive_utc_now()
    invoice.refunded_at = None
    invoice.refund_reason = None

    database.add(invoice)
    database.commit()

    return get_invoice(database, invoice.id)


def refund_invoice(
    database: Session,
    invoice_id: int,
    refund_reason: str,
) -> Invoice:
    """Refund a paid invoice."""

    invoice = get_invoice(database, invoice_id)

    if invoice.payment_status != PaymentStatus.PAID:
        raise AppException(
            message="Only paid invoices can be refunded.",
            status_code=409,
        )

    invoice.payment_status = PaymentStatus.REFUNDED
    invoice.refunded_at = naive_utc_now()
    invoice.refund_reason = refund_reason

    database.add(invoice)
    database.commit()

    return get_invoice(database, invoice.id)