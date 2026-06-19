from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


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

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

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
