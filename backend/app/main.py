"""FastAPI application entry point."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import datetime, timezone
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.routers.auth import router as auth_router
from app.api.routers.customers import (
    router as customers_router,
)
from app.api.routers.invoices import (
    router as invoices_router,
)
from app.api.routers.menu import router as menu_router
from app.api.routers.orders import router as orders_router
from app.api.routers.reports import router as reports_router
from app.api.routers.reservations import (
    router as reservations_router,
)
from app.api.routers.settings import router as settings_router
from app.api.routers.tables import router as tables_router
from app.core.config import settings
from app.core.exceptions import register_exception_handlers
from app.core.responses import success_response


logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format=(
        "%(asctime)s | %(levelname)s | "
        "%(name)s | %(message)s"
    ),
)

logger = logging.getLogger(__name__)


def create_upload_directories() -> None:
    """Create required local upload directories."""

    settings.upload_path.mkdir(
        parents=True,
        exist_ok=True,
    )

    settings.menu_upload_path.mkdir(
        parents=True,
        exist_ok=True,
    )

    settings.restaurant_upload_path.mkdir(
        parents=True,
        exist_ok=True,
    )


@asynccontextmanager
async def lifespan(
    application: FastAPI,
) -> AsyncIterator[None]:
    """Run application startup and shutdown tasks."""

    del application

    create_upload_directories()

    logger.info(
        "%s %s started in %s mode",
        settings.app_name,
        settings.app_version,
        settings.app_env,
    )

    yield

    logger.info("%s stopped", settings.app_name)


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=(
        "REST API for the LazyBites "
        "Restaurant Management System."
    ),
    debug=settings.debug,
    docs_url=(
        "/docs"
        if settings.is_development
        else None
    ),
    redoc_url=(
        "/redoc"
        if settings.is_development
        else None
    ),
    openapi_url=(
        "/openapi.json"
        if settings.is_development
        else None
    ),
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_exception_handlers(app)

create_upload_directories()

app.mount(
    "/uploads",
    StaticFiles(
        directory=str(settings.upload_path)
    ),
    name="uploads",
)

app.include_router(
    auth_router,
    prefix=settings.api_v1_prefix,
)

app.include_router(
    settings_router,
    prefix=settings.api_v1_prefix,
)

app.include_router(
    tables_router,
    prefix=settings.api_v1_prefix,
)

app.include_router(
    reservations_router,
    prefix=settings.api_v1_prefix,
)

app.include_router(
    menu_router,
    prefix=settings.api_v1_prefix,
)

app.include_router(
    orders_router,
    prefix=settings.api_v1_prefix,
)

app.include_router(
    invoices_router,
    prefix=settings.api_v1_prefix,
)

app.include_router(
    customers_router,
    prefix=settings.api_v1_prefix,
)

app.include_router(
    reports_router,
    prefix=settings.api_v1_prefix,
)


@app.get(
    "/",
    tags=["System"],
    summary="API information",
)
def read_root():
    """Return basic API information."""

    return success_response(
        message="LazyBites API is running.",
        data={
            "application": settings.app_name,
            "version": settings.app_version,
            "environment": settings.app_env,
            "api_prefix": settings.api_v1_prefix,
            "documentation": (
                "/docs"
                if settings.is_development
                else None
            ),
        },
    )


@app.get(
    "/health",
    tags=["System"],
    summary="Health check",
)
def health_check():
    """Return application health information."""

    return success_response(
        message="Application is healthy.",
        data={
            "status": "healthy",
            "timestamp": datetime.now(
                timezone.utc
            ).isoformat(),
        },
    )


@app.get(
    f"{settings.api_v1_prefix}/health",
    tags=["System"],
    summary="Versioned health check",
)
def versioned_health_check():
    """Return versioned health information."""

    return success_response(
        message="Application is healthy.",
        data={
            "status": "healthy",
            "version": settings.app_version,
            "timestamp": datetime.now(
                timezone.utc
            ).isoformat(),
        },
    )