import logging
import warnings
from functools import lru_cache
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    app_name: str = "UNSAID Commerce API"
    environment: str = "local"
    debug: bool = False
    database_url: str = "sqlite+aiosqlite:///./unsaid.db"
    cors_origins: list[str] = Field(
        default_factory=lambda: [
            "http://localhost:3000",
            "http://localhost:5173",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:5173",
        ]
    )
    static_dir: Path = Path(__file__).resolve().parents[1] / "static"
    campaign_img_dir: Path = Path(__file__).resolve().parents[1] / "img"
    templates_dir: Path = Path(__file__).resolve().parents[1] / "templates"
    whatsapp_business_number: str = "15551234567"
    groq_api_key: str = ""
    groq_model: str = "llama-3.3-70b-versatile"
    session_secret_key: str = "change-me-in-production"
    session_cookie_name: str = "unsaid_session"
    session_cookie_secure: bool = False
    admin_bootstrap_email: str = ""
    admin_bootstrap_password: str = ""
    log_file: str = ""
    enable_hsts: bool = False
    enable_rate_limit: bool = True
    site_url: str = "http://localhost:8000"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @field_validator("session_secret_key")
    @classmethod
    def validate_session_secret_key(cls, value: str) -> str:
        if value == "change-me-in-production":
            warnings.warn(
                "CRITICAL: session_secret_key is still the default value. "
                "Set a strong secret in production.",
                RuntimeWarning,
                stacklevel=2,
            )
            logger.warning(
                "CRITICAL: session_secret_key is still the default value 'change-me-in-production'."
            )
        return value

    @field_validator("database_url", mode="before")
    @classmethod
    def normalize_database_url(cls, value: object) -> object:
        if not isinstance(value, str):
            return value

        normalized_value = value.strip()
        postgres_schemes = (
            "postgres://",
            "postgresql://",
            "postgresql+psycopg://",
            "postgresql+psycopg2://",
        )

        for scheme in postgres_schemes:
            if normalized_value.startswith(scheme):
                normalized_value = "postgresql+asyncpg://" + normalized_value[len(scheme) :]
                break

        if not normalized_value.startswith("postgresql+asyncpg://"):
            return normalized_value

        split_url = urlsplit(normalized_value)
        query_params = parse_qsl(split_url.query, keep_blank_values=True)
        has_required_sslmode = False
        filtered_params: list[tuple[str, str]] = []

        for key, param_value in query_params:
            if key == "channel_binding":
                continue

            if key == "sslmode" and param_value == "require":
                has_required_sslmode = True
                continue

            if key == "ssl" and has_required_sslmode:
                continue

            filtered_params.append((key, param_value))

        if has_required_sslmode:
            filtered_params = [
                (key, param_value) for key, param_value in filtered_params if key != "ssl"
            ]
            filtered_params.append(("ssl", "require"))

        return urlunsplit(split_url._replace(query=urlencode(filtered_params)))

    @field_validator("debug", mode="before")
    @classmethod
    def parse_debug(cls, value: bool | str) -> bool:
        if isinstance(value, bool):
            return value

        normalized_value = value.strip().lower()
        if normalized_value in {"1", "true", "yes", "on", "debug", "local"}:
            return True

        if normalized_value in {"0", "false", "no", "off", "release", "prod"}:
            return False

        return False

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: str | list[str]) -> list[str]:
        if isinstance(value, list):
            return value

        if not value:
            return []

        stripped_value = value.strip()
        if stripped_value.startswith("["):
            return [origin.strip().strip('"') for origin in stripped_value[1:-1].split(",")]

        return [origin.strip() for origin in stripped_value.split(",")]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
