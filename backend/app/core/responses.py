"""Reusable API response helpers."""

from typing import Any

from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse


def success_response(
    *,
    message: str,
    data: Any = None,
    status_code: int = 200,
) -> JSONResponse:
    """Return a standard successful API response."""

    content = {
        "success": True,
        "message": message,
        "data": data,
    }

    return JSONResponse(
        status_code=status_code,
        content=jsonable_encoder(content),
    )


def error_response(
    *,
    message: str,
    status_code: int,
    errors: list[dict[str, Any]] | None = None,
) -> JSONResponse:
    """Return a standard failed API response."""

    content = {
        "success": False,
        "message": message,
        "errors": errors or [],
    }

    return JSONResponse(
        status_code=status_code,
        content=jsonable_encoder(content),
    )