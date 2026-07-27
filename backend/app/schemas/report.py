"""Schemas for dashboard and restaurant reports."""

from datetime import date
from decimal import Decimal

from pydantic import BaseModel

from app.utils.enums import (
    OrderStatus,
    PaymentMethod,
    ReservationStatus,
)


class DashboardSummaryResponse(BaseModel):
    """Main dashboard totals."""

    today_revenue: Decimal
    today_orders: int
    pending_orders: int
    active_reservations: int
    total_customers: int
    unpaid_invoices: int


class SalesSummaryResponse(BaseModel):
    """Sales totals for a selected period."""

    start_date: date
    end_date: date

    paid_invoice_count: int
    refunded_invoice_count: int
    unpaid_invoice_count: int

    gross_paid_revenue: Decimal
    refunded_revenue: Decimal
    net_revenue: Decimal

    total_discount: Decimal
    total_gst: Decimal
    average_paid_invoice: Decimal


class StatusCountResponse(BaseModel):
    """Count grouped by a status value."""

    status: str
    count: int


class PaymentBreakdownResponse(BaseModel):
    """Paid invoice totals grouped by payment method."""

    payment_method: PaymentMethod
    invoice_count: int
    total_amount: Decimal


class PopularItemResponse(BaseModel):
    """Frequently sold menu item information."""

    menu_item_id: int
    item_name: str
    quantity_sold: int
    sales_amount: Decimal


class ReportsResponse(BaseModel):
    """Complete report result for one date period."""

    sales: SalesSummaryResponse
    order_statuses: list[StatusCountResponse]
    reservation_statuses: list[StatusCountResponse]
    payment_breakdown: list[PaymentBreakdownResponse]
    popular_items: list[PopularItemResponse]