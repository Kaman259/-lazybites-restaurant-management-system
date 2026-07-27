"""Database engine, session factory, and request dependency."""

from collections.abc import Generator

from sqlalchemy import Engine, create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings


def get_engine_options() -> dict:
    """Return database-specific SQLAlchemy engine options."""

    options: dict = {
        "echo": settings.sql_echo,
        "pool_pre_ping": True,
    }

    if settings.database_url.startswith("sqlite"):
        options["connect_args"] = {"check_same_thread": False}

    return options


engine = create_engine(
    settings.database_url,
    **get_engine_options(),
)

SessionLocal = sessionmaker(
    bind=engine,
    class_=Session,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)


if settings.database_url.startswith("sqlite"):

    @event.listens_for(Engine, "connect")
    def enable_sqlite_foreign_keys(
        database_connection: object,
        connection_record: object,
    ) -> None:
        """Enable foreign-key enforcement for SQLite connections."""

        del connection_record

        cursor = database_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


def get_db() -> Generator[Session, None, None]:
    """Provide one SQLAlchemy session for an API request."""

    database_session = SessionLocal()

    try:
        yield database_session
    finally:
        database_session.close()