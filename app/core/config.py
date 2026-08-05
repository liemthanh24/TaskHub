import os
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict

ENV_FILES = {
    "dev": ".env.dev",
    "test": ".env.test",
    "prod": ".env.prod",
}

DEFAULT_JWT_SECRET = "change-me-in-production"
DEFAULT_SQLITE_URL = "sqlite+aiosqlite:///./taskhub.db"


def _resolve_env_file() -> str:
    env = os.getenv("APP_ENV", "").lower().strip()
    if not env:
        for name, path in ENV_FILES.items():
            if os.path.exists(path):
                env = name
                break
        else:
            env = "dev"
    candidate = ENV_FILES.get(env)
    if candidate and os.path.exists(candidate):
        return candidate
    return ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=_resolve_env_file(),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    APP_NAME: str = "TaskHub API"
    APP_VERSION: str = "0.3.0"
    APP_ENV: Literal["dev", "test", "prod"] = "dev"
    DEBUG: bool = False

    DATABASE_URL: str = DEFAULT_SQLITE_URL
    LOG_LEVEL: str = "INFO"
    CORS_ORIGINS: str = "*"

    JWT_SECRET: str = DEFAULT_JWT_SECRET
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60

    ADMIN_EMAIL: str = ""
    ADMIN_PASSWORD: str = ""

    REDIS_URL: str = ""

    def validate(self) -> None:
        errors: list[str] = []
        if self.JWT_EXPIRE_MINUTES <= 0:
            errors.append("JWT_EXPIRE_MINUTES must be a positive integer")

        if self.APP_ENV == "prod":
            if self.JWT_SECRET == DEFAULT_JWT_SECRET:
                errors.append("JWT_SECRET must be set in production (do not use the default)")
            if not self.DATABASE_URL or self.DATABASE_URL == DEFAULT_SQLITE_URL:
                errors.append("DATABASE_URL must point to a real database in production")
            if not self.ADMIN_PASSWORD:
                errors.append("ADMIN_PASSWORD must be set in production")

        if errors:
            raise RuntimeError("Invalid settings: " + "; ".join(errors))

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.validate()


settings = Settings()
