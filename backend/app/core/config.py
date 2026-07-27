"""Application configuration loaded from environment variables."""

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central application configuration."""

    app_name: str = "LazyBites Restaurant Management System"
    app_version: str = "1.0.0"
    app_env: str = "development"
    debug: bool = True

    api_v1_prefix: str = "/api/v1"

    database_url: str = "sqlite:///./restaurant.db"
    sql_echo: bool = False

    frontend_url: str = "http://localhost:5173"
    cors_origins: str = "http://localhost:5173"

    upload_directory: str = "uploads"
    max_upload_size_mb: int = Field(default=5, gt=0, le=25)

    firebase_credentials_path: str = "firebase-service-account.json"
    firebase_check_revoked: bool = False

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def cors_origin_list(self) -> list[str]:
        """Return configured browser origins as a clean list."""

        origins = [
            origin.strip()
            for origin in self.cors_origins.split(",")
            if origin.strip()
        ]

        if self.frontend_url not in origins:
            origins.append(self.frontend_url)

        return origins

    @property
    def upload_path(self) -> Path:
        """Return the absolute upload directory path."""

        return Path(self.upload_directory).resolve()

    @property
    def menu_upload_path(self) -> Path:
        """Return the menu-item upload directory."""

        return self.upload_path / "menu-items"

    @property
    def restaurant_upload_path(self) -> Path:
        """Return the restaurant upload directory."""

        return self.upload_path / "restaurant"

    @property
    def firebase_credentials_file(self) -> Path:
        """Return the absolute Firebase credentials path."""

        return Path(self.firebase_credentials_path).resolve()

    @property
    def is_development(self) -> bool:
        """Return whether the application uses development settings."""

        return self.app_env.lower() == "development"


@lru_cache
def get_settings() -> Settings:
    """Create and cache one settings object."""

    return Settings()


settings = get_settings()