"""Application exceptions and FastAPI exception handlers."""

import logging
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.config import settings
from app.core.responses import error_response


logger = logging.getLogger(__name__)


class AppException(Exception):
    """Expected application error with a safe client message."""

    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        errors: list[dict[str, Any]] | None = None,
    ) -> None:
        self.message = message
        self.status_code = status_code
        self.errors = errors or []
        super().__init__(message)


async def app_exception_handler(
    request: Request,
    exception: AppException,
):
    """Handle expected business-rule errors."""

    del request

    return error_response(
        message=exception.message,
        status_code=exception.status_code,
        errors=exception.errors,
    )


async def http_exception_handler(
    request: Request,
    exception: StarletteHTTPException,
):
    """Convert HTTP exceptions into the project response format."""

    del request

    if isinstance(exception.detail, str):
        message = exception.detail
        errors: list[dict[str, Any]] = []
    else:
        message = "The request could not be completed."
        errors = [{"detail": exception.detail}]

    return error_response(
        message=message,
        status_code=exception.status_code,
        errors=errors,
    )


async def validation_exception_handler(
    request: Request,
    exception: RequestValidationError,
):
    """Return readable Pydantic validation errors."""

    del request

    errors: list[dict[str, Any]] = []

    for error in exception.errors():
        location_parts = [
            str(part)
            for part in error.get("loc", [])
            if part not in {"body", "query", "path", "header"}
        ]

        errors.append(
            {
                "field": ".".join(location_parts) or "request",
                "message": error.get("msg", "Invalid value"),
                "type": error.get("type", "validation_error"),
            }
        )

    return error_response(
        message="Please correct the invalid request data.",
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        errors=errors,
    )


async def database_exception_handler(
    request: Request,
    exception: SQLAlchemyError,
):
    """Handle unexpected database errors without leaking SQL details."""

    logger.exception(
        "Database error while processing %s %s",
        request.method,
        request.url.path,
        exc_info=exception,
    )

    return error_response(
        message="A database error occurred. Please try again.",
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )


async def unexpected_exception_handler(
    request: Request,
    exception: Exception,
):
    """Handle unplanned server errors."""

    logger.exception(
        "Unexpected error while processing %s %s",
        request.method,
        request.url.path,
        exc_info=exception,
    )

    errors: list[dict[str, Any]] = []

    if settings.debug:
        errors.append(
            {
                "type": exception.__class__.__name__,
                "message": str(exception),
            }
        )

    return error_response(
        message="An unexpected server error occurred.",
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        errors=errors,
    )


def register_exception_handlers(application: FastAPI) -> None:
    """Register all project exception handlers."""

    application.add_exception_handler(
        AppException,
        app_exception_handler,
    )
    application.add_exception_handler(
        StarletteHTTPException,
        http_exception_handler,
    )
    application.add_exception_handler(
        RequestValidationError,
        validation_exception_handler,
    )
    application.add_exception_handler(
        SQLAlchemyError,
        database_exception_handler,
    )
    application.add_exception_handler(
        Exception,
        unexpected_exception_handler,
    )