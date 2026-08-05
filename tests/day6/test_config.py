import pytest

from app.core.config import DEFAULT_JWT_SECRET, DEFAULT_SQLITE_URL, Settings


def _prod_settings(**overrides) -> Settings:
    base = {
        "APP_ENV": "prod",
        "JWT_SECRET": "a-strong-production-secret",
        "DATABASE_URL": "postgresql+asyncpg://user:pass@localhost:5432/taskhub",
        "ADMIN_PASSWORD": "admin-secret",
    }
    base.update(overrides)
    return Settings(_env_file=None, **base)


def test_prod_rejects_default_jwt_secret():
    with pytest.raises(RuntimeError, match="JWT_SECRET"):
        _prod_settings(JWT_SECRET=DEFAULT_JWT_SECRET)


def test_prod_rejects_default_sqlite_url():
    with pytest.raises(RuntimeError, match="DATABASE_URL"):
        _prod_settings(DATABASE_URL=DEFAULT_SQLITE_URL)


def test_prod_requires_admin_password():
    with pytest.raises(RuntimeError, match="ADMIN_PASSWORD"):
        _prod_settings(ADMIN_PASSWORD="")


def test_prod_rejects_non_positive_token_expiry():
    with pytest.raises(RuntimeError, match="JWT_EXPIRE_MINUTES"):
        _prod_settings(JWT_EXPIRE_MINUTES=0)


def test_valid_prod_settings_pass():
    s = _prod_settings()
    assert s.APP_ENV == "prod"
    assert s.JWT_SECRET == "a-strong-production-secret"


def test_dev_allows_default_secret_and_sqlite():
    s = Settings(
        _env_file=None,
        APP_ENV="dev",
        JWT_SECRET=DEFAULT_JWT_SECRET,
        DATABASE_URL=DEFAULT_SQLITE_URL,
        ADMIN_PASSWORD="",
    )
    assert s.APP_ENV == "dev"
    assert s.DEBUG is False
