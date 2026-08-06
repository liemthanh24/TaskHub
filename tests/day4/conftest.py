import asyncio

import pytest
from fastapi.testclient import TestClient

from app.core.cache import cache
from app.core.config import settings
from app.core.security import hash_password
from app.database import AsyncSessionLocal, engine, init_db
from app.main import app
from app.models.base import Base
from app.repositories.user import UserRepository


def _flush_cache():
    if not settings.REDIS_URL:
        asyncio.run(cache.flush())


@pytest.fixture(autouse=True)
def clean_state():
    asyncio.run(init_db())
    _flush_cache()
    yield
    async def _cleanup():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
    asyncio.run(_cleanup())
    _flush_cache()


@pytest.fixture
def client():
    return TestClient(app)


def register(
    client: TestClient,
    email: str = "user@example.com",
    password: str = "secret123",
) -> str:
    resp = client.post("/auth/register", json={"email": email, "password": password})
    assert resp.status_code == 201, resp.text
    return resp.json()["access_token"]


def create_admin_token(email: str = "admin@example.com") -> str:
    from app.core.security import create_access_token

    async def _make():
        async with AsyncSessionLocal() as session:
            repo = UserRepository(session)
            user = await repo.create(
                email=email,
                hashed_password=hash_password("secret123"),
                role="admin",
            )
            return user.id
    user_id = asyncio.run(_make())
    return create_access_token(user_id)


@pytest.fixture
def user_token(client):
    return register(client)


@pytest.fixture
def user2_token(client):
    return register(client, email="user2@example.com")


@pytest.fixture
def admin_token(client):
    return create_admin_token()


def headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}
