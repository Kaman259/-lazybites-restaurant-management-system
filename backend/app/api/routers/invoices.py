"""Invoice, payment, and refund endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.dependencies import DatabaseSession
from app.auth.permissions import require_staff_or_admin
from app.core.responses import success_response
from app.models.user import User
from app.schemas.invoice import (
    InvoiceCreate,
    InvoicePaymentUpdate,
    InvoiceRefundUpdate,
    InvoiceResponse,
)
from app.services.invoice_service import (
    create_invoice,
    get_invoice,
    list_invoices,
    mark_invoice_paid,
    refund_invoice,
)
from app.utils.enums import (
    PaymentMethod,
    PaymentStatus,
)


router = APIRouter(
    prefix="/invoices",
    tags=["Invoices"],
)

StaffUser = Annotated[
    User,
    Depends(require_staff_or_admin),
]


def serialise_invoice(invoice):
    """Convert an invoice into API response data."""

    response_data = InvoiceResponse.model_validate(
        invoice
    )

    return response_data.model_dump(mode="json")


@router.post("", status_code=201)
def add_invoice(
    invoice_data: InvoiceCreate,
    database: DatabaseSession,
    current_user: StaffUser,
):
    """Generate an invoice from a completed order."""

    del current_user

    invoice = create_invoice(
        database=database,
        invoice_data=invoice_data,
    )

    return success_response(
        message="Invoice generated successfully.",
        data=serialise_invoice(invoice),
        status_code=201,
    )


@router.get("")
def read_invoices(
    database: DatabaseSession,
    current_user: StaffUser,
    payment_status: PaymentStatus | None = Query(
        default=None
    ),
    payment_method: PaymentMethod | None = Query(
        default=None
    ),
):
    """Return filtered invoice records."""

    del current_user

    invoices = list_invoices(
        database=database,
        payment_status=payment_status,
        payment_method=payment_method,
    )

    return success_response(
        message="Invoices retrieved successfully.",
        data=[
            serialise_invoice(invoice)
            for invoice in invoices
        ],
    )


@router.get("/{invoice_id}")
def read_invoice(
    invoice_id: int,
    database: DatabaseSession,
    current_user: StaffUser,
):
    """Return one invoice."""

    del current_user

    invoice = get_invoice(database, invoice_id)

    return success_response(
        message="Invoice retrieved successfully.",
        data=serialise_invoice(invoice),
    )


@router.patch("/{invoice_id}/payment")
def pay_invoice(
    invoice_id: int,
    payment_data: InvoicePaymentUpdate,
    database: DatabaseSession,
    current_user: StaffUser,
):
    """Mark an invoice as paid."""

    del current_user

    invoice = mark_invoice_paid(
        database=database,
        invoice_id=invoice_id,
        payment_method=payment_data.payment_method,
    )

    return success_response(
        message="Invoice marked as paid successfully.",
        data=serialise_invoice(invoice),
    )


@router.patch("/{invoice_id}/refund")
def process_invoice_refund(
    invoice_id: int,
    refund_data: InvoiceRefundUpdate,
    database: DatabaseSession,
    current_user: StaffUser,
):
    """Refund a paid invoice."""

    del current_user

    invoice = refund_invoice(
        database=database,
        invoice_id=invoice_id,
        refund_reason=refund_data.refund_reason,
    )

    return success_response(
        message="Invoice refunded successfully.",
        data=serialise_invoice(invoice),
    )