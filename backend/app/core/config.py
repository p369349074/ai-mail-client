from functools import cached_property

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "ai-mail-client-api"
    app_version: str = "0.1.0"
    app_env: str = "development"
    database_url: str = "sqlite:///./dev.db"
    secret_key: str = "change-me"
    cors_origins: str = "http://localhost:5173"
    default_user_email: str = "local@example.invalid"
    default_user_display_name: str = "Local User"
    mail_connect_timeout_seconds: int = Field(default=10, ge=1, le=60)

    max_initial_days: int = 30
    max_initial_messages: int = 1000
    max_body_cache_mb: int = 1024
    max_attachment_cache_mb: int = 700
    disk_pause_threshold: int = Field(default=85, ge=1, le=100)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @cached_property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


settings = Settings()
