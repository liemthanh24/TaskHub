import asyncio

import pytest
from fastapi.testclient import TestClient

from app.core.cache import cache
from app.core.config import settings
from app.core.queue import task_queue
from app.database import engine, init_db
from app.main import app
from app.models.base import Base


def _flush_cache():
    if not settings.REDIS_URL:
        asyncio.run(cache.flush())


@pytest.fixture(autouse=True)
def clean_state():
    asyncio.run(task_queue.reset())
    asyncio.run(init_db())
    _flush_cache()
    yield
    async def _cleanup():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
    asyncio.run(_cleanup())
    asyncio.run(task_queue.reset())
    _flush_cache()


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


def register(client: TestClient, email: str = "user@example.com") -> str:
    resp = client.post("/auth/register", json={"email": email, "password": "secret123"})
    assert resp.status_code == 201, resp.text
    return resp.json()["access_token"]


@pytest.fixture
def user_token(client):
    return register(client)


@pytest.fixture
def user2_token(client):
    return register(client, email="user2@example.com")


def headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}
