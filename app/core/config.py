from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    APP_NAME: str = "TaskHub API"
    APP_VERSION: str = "0.2.0"
    DEBUG: bool = False

    DATABASE_URL: str = "sqlite+aiosqlite:///./taskhub.db"
    LOG_LEVEL: str = "INFO"
    CORS_ORIGINS: str = "*"

    JWT_SECRET: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60

    ADMIN_EMAIL: str = ""
    ADMIN_PASSWORD: str = ""

    REDIS_URL: str = ""

settings = Settings()

