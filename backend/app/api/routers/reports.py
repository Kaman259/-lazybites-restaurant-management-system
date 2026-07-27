"""Dashboard and reporting endpoints."""

from datetime import date, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.dependencies import DatabaseSession
from app.auth.permissions import (
    require_admin,
    require_staff_or_admin,
)
from app.core.exceptions import AppException
from app.core.responses import success_response
from app.models.user import User
from app.schemas.report import (
    DashboardSummaryResponse,
    ReportsResponse,
)
from app.services.report_service import (
    get_dashboard_summary,
    get_reports,
)


router = APIRouter(
    prefix="/reports",
    tags=["Reports"],
)

StaffUser = Annotated[
    User,
    Depends(require_staff_or_admin),
]

AdminUser = Annotated[
    User,
    Depends(require_admin),
]


@router.get("/dashboard")
def read_dashboard_summary(
    database: DatabaseSession,
    current_user: StaffUser,
):
    """Return dashboard information."""

    del current_user

    report_data = get_dashboard_summary(database)

    response_data = (
        DashboardSummaryResponse.model_validate(
            report_data
        )
    )

    return success_response(
        message="Dashboard summary retrieved successfully.",
        data=response_data.model_dump(mode="json"),
    )


@router.get("/summary")
def read_reports(
    database: DatabaseSession,
    current_user: AdminUser,
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
):
    """Return restaurant reports for a date range."""

    del current_user

    selected_end_date = end_date or date.today()
    selected_start_date = (
        start_date
        or selected_end_date - timedelta(days=29)
    )

    if selected_start_date > selected_end_date:
        raise AppException(
            message=(
                "Start date cannot be after end date."
            ),
            status_code=400,
        )

    if (
        selected_end_date - selected_start_date
    ).days > 366:
        raise AppException(
            message=(
                "The report period cannot exceed 367 days."
            ),
            status_code=400,
        )

    report_data = get_reports(
        database=database,
        start_date=selected_start_date,
        end_date=selected_end_date,
    )

    response_data = ReportsResponse.model_validate(
        report_data
    )

    return success_response(
        message="Reports retrieved successfully.",
        data=response_data.model_dump(mode="json"),
    )