from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "emr-service"
    environment: str = "dev"
    debug: bool = False
    api_v1_prefix: str = "/api/v1"

    database_url: str = Field(
        default="postgresql+asyncpg://postgres:postgres@db:5432/emr",
    )

    jwt_secret_key: str = Field(
        default="0123456789abcdef0123456789abcdef",
        min_length=16,
    )
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    log_level: str = "INFO"
    log_file_path: str = "logs/app.log"

    admin_login: str = "admin"
    admin_password: str = Field(default="AdminPass123", min_length=8)
    admin_full_name: str = "System Administrator"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


def get_settings() -> Settings:
    return Settings()
