"""Dashboard and restaurant reporting service functions."""

from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal
from zoneinfo import ZoneInfo

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.customer import Customer
from app.models.invoice import Invoice
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.reservation import Reservation
from app.services.settings_service import get_restaurant_settings
from app.utils.enums import (
    OrderStatus,
    PaymentStatus,
    ReservationStatus,
)


def money(value) -> Decimal:
    """Return a two-decimal monetary value."""

    return Decimal(value or 0).quantize(Decimal("0.01"))


def utc_database_range(
    start_date: date,
    end_date: date,
    timezone_name: str,
) -> tuple[datetime, datetime]:
    """Convert local date limits to naive UTC datetimes."""

    local_timezone = ZoneInfo(timezone_name)

    local_start = datetime.combine(
        start_date,
        time.min,
        tzinfo=local_timezone,
    )

    local_end = datetime.combine(
        end_date + timedelta(days=1),
        time.min,
        tzinfo=local_timezone,
    )

    utc_start = (
        local_start.astimezone(timezone.utc)
        .replace(tzinfo=None)
    )

    utc_end = (
        local_end.astimezone(timezone.utc)
        .replace(tzinfo=None)
    )

    return utc_start, utc_end


def get_dashboard_summary(
    database: Session,
) -> dict:
    """Return current-day dashboard totals."""

    settings_record = get_restaurant_settings(database)

    local_today = datetime.now(
        ZoneInfo(settings_record.timezone)
    ).date()

    utc_start, utc_end = utc_database_range(
        start_date=local_today,
        end_date=local_today,
        timezone_name=settings_record.timezone,
    )

    paid_today = money(
        database.scalar(
            select(
                func.coalesce(
                    func.sum(Invoice.grand_total),
                    0,
                )
            ).where(
                Invoice.payment_status.in_(
                    [
                        PaymentStatus.PAID,
                        PaymentStatus.REFUNDED,
                    ]
                ),
                Invoice.paid_at >= utc_start,
                Invoice.paid_at < utc_end,
            )
        )
    )

    refunded_today = money(
        database.scalar(
            select(
                func.coalesce(
                    func.sum(Invoice.grand_total),
                    0,
                )
            ).where(
                Invoice.payment_status
                == PaymentStatus.REFUNDED,
                Invoice.refunded_at >= utc_start,
                Invoice.refunded_at < utc_end,
            )
        )
    )

    today_orders = database.scalar(
        select(func.count(Order.id)).where(
            Order.created_at >= utc_start,
            Order.created_at < utc_end,
        )
    )

    pending_orders = database.scalar(
        select(func.count(Order.id)).where(
            Order.status.in_(
                [
                    OrderStatus.PENDING,
                    OrderStatus.PREPARING,
                    OrderStatus.READY,
                    OrderStatus.SERVED,
                ]
            )
        )
    )

    active_reservations = database.scalar(
        select(func.count(Reservation.id)).where(
            Reservation.status.in_(
                [
                    ReservationStatus.PENDING,
                    ReservationStatus.CONFIRMED,
                    ReservationStatus.SEATED,
                ]
            ),
            Reservation.end_time >= utc_start,
            Reservation.start_time < utc_end,
        )
    )

    total_customers = database.scalar(
        select(func.count(Customer.id)).where(
            Customer.is_active.is_(True)
        )
    )

    unpaid_invoices = database.scalar(
        select(func.count(Invoice.id)).where(
            Invoice.payment_status
            == PaymentStatus.UNPAID
        )
    )

    return {
        "today_revenue": money(
            paid_today - refunded_today
        ),
        "today_orders": today_orders or 0,
        "pending_orders": pending_orders or 0,
        "active_reservations": (
            active_reservations or 0
        ),
        "total_customers": total_customers or 0,
        "unpaid_invoices": unpaid_invoices or 0,
    }


def get_reports(
    database: Session,
    start_date: date,
    end_date: date,
) -> dict:
    """Return reports for a selected local date range."""

    settings_record = get_restaurant_settings(database)

    utc_start, utc_end = utc_database_range(
        start_date=start_date,
        end_date=end_date,
        timezone_name=settings_record.timezone,
    )

    received_payment_statuses = [
        PaymentStatus.PAID,
        PaymentStatus.REFUNDED,
    ]

    paid_invoice_count = database.scalar(
        select(func.count(Invoice.id)).where(
            Invoice.payment_status == PaymentStatus.PAID,
            Invoice.paid_at >= utc_start,
            Invoice.paid_at < utc_end,
        )
    ) or 0

    refunded_invoice_count = database.scalar(
        select(func.count(Invoice.id)).where(
            Invoice.payment_status
            == PaymentStatus.REFUNDED,
            Invoice.refunded_at >= utc_start,
            Invoice.refunded_at < utc_end,
        )
    ) or 0

    unpaid_invoice_count = database.scalar(
        select(func.count(Invoice.id)).where(
            Invoice.payment_status
            == PaymentStatus.UNPAID,
            Invoice.created_at >= utc_start,
            Invoice.created_at < utc_end,
        )
    ) or 0

    received_invoice_count = database.scalar(
        select(func.count(Invoice.id)).where(
            Invoice.payment_status.in_(
                received_payment_statuses
            ),
            Invoice.paid_at >= utc_start,
            Invoice.paid_at < utc_end,
        )
    ) or 0

    gross_paid_revenue = money(
        database.scalar(
            select(
                func.coalesce(
                    func.sum(Invoice.grand_total),
                    0,
                )
            ).where(
                Invoice.payment_status.in_(
                    received_payment_statuses
                ),
                Invoice.paid_at >= utc_start,
                Invoice.paid_at < utc_end,
            )
        )
    )

    refunded_revenue = money(
        database.scalar(
            select(
                func.coalesce(
                    func.sum(Invoice.grand_total),
                    0,
                )
            ).where(
                Invoice.payment_status
                == PaymentStatus.REFUNDED,
                Invoice.refunded_at >= utc_start,
                Invoice.refunded_at < utc_end,
            )
        )
    )

    invoice_period_filter = (
        Invoice.created_at >= utc_start,
        Invoice.created_at < utc_end,
    )

    total_discount = money(
        database.scalar(
            select(
                func.coalesce(
                    func.sum(Invoice.discount_amount),
                    0,
                )
            ).where(*invoice_period_filter)
        )
    )

    total_gst = money(
        database.scalar(
            select(
                func.coalesce(
                    func.sum(Invoice.gst_amount),
                    0,
                )
            ).where(*invoice_period_filter)
        )
    )

    average_paid_invoice = money(
        (
            gross_paid_revenue / received_invoice_count
            if received_invoice_count
            else Decimal("0.00")
        )
    )

    order_status_rows = database.execute(
        select(
            Order.status,
            func.count(Order.id),
        )
        .where(
            Order.created_at >= utc_start,
            Order.created_at < utc_end,
        )
        .group_by(Order.status)
        .order_by(Order.status)
    ).all()

    reservation_status_rows = database.execute(
        select(
            Reservation.status,
            func.count(Reservation.id),
        )
        .where(
            Reservation.created_at >= utc_start,
            Reservation.created_at < utc_end,
        )
        .group_by(Reservation.status)
        .order_by(Reservation.status)
    ).all()

    payment_rows = database.execute(
        select(
            Invoice.payment_method,
            func.count(Invoice.id),
            func.coalesce(
                func.sum(Invoice.grand_total),
                0,
            ),
        )
        .where(
            Invoice.payment_status.in_(
                received_payment_statuses
            ),
            Invoice.payment_method.is_not(None),
            Invoice.paid_at >= utc_start,
            Invoice.paid_at < utc_end,
        )
        .group_by(Invoice.payment_method)
        .order_by(Invoice.payment_method)
    ).all()

    popular_item_rows = database.execute(
        select(
            OrderItem.menu_item_id,
            OrderItem.item_name,
            func.sum(OrderItem.quantity),
            func.sum(OrderItem.line_total),
        )
        .join(Order, OrderItem.order_id == Order.id)
        .join(Invoice, Invoice.order_id == Order.id)
        .where(
            Invoice.payment_status.in_(
                received_payment_statuses
            ),
            Invoice.paid_at >= utc_start,
            Invoice.paid_at < utc_end,
        )
        .group_by(
            OrderItem.menu_item_id,
            OrderItem.item_name,
        )
        .order_by(
            func.sum(OrderItem.quantity).desc()
        )
        .limit(10)
    ).all()

    return {
        "sales": {
            "start_date": start_date,
            "end_date": end_date,
            "paid_invoice_count": paid_invoice_count,
            "refunded_invoice_count": (
                refunded_invoice_count
            ),
            "unpaid_invoice_count": (
                unpaid_invoice_count
            ),
            "gross_paid_revenue": gross_paid_revenue,
            "refunded_revenue": refunded_revenue,
            "net_revenue": money(
                gross_paid_revenue - refunded_revenue
            ),
            "total_discount": total_discount,
            "total_gst": total_gst,
            "average_paid_invoice": (
                average_paid_invoice
            ),
        },
        "order_statuses": [
            {
                "status": status.value,
                "count": count,
            }
            for status, count in order_status_rows
        ],
        "reservation_statuses": [
            {
                "status": status.value,
                "count": count,
            }
            for status, count
            in reservation_status_rows
        ],
        "payment_breakdown": [
            {
                "payment_method": payment_method,
                "invoice_count": invoice_count,
                "total_amount": money(total_amount),
            }
            for (
                payment_method,
                invoice_count,
                total_amount,
            ) in payment_rows
        ],
        "popular_items": [
            {
                "menu_item_id": menu_item_id,
                "item_name": item_name,
                "quantity_sold": quantity_sold,
                "sales_amount": money(sales_amount),
            }
            for (
                menu_item_id,
                item_name,
                quantity_sold,
                sales_amount,
            ) in popular_item_rows
        ],
    }