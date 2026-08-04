import asyncio

import pytest
from fastapi.testclient import TestClient

from app.database import engine, init_db
from app.main import app
from app.models.base import Base


@pytest.fixture(autouse=True)
def clean_db():
    asyncio.run(init_db())
    yield
    async def _drop():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
    asyncio.run(_drop())


@pytest.fixture
def client():
    return TestClient(app)


def register(client: TestClient, email: str = "user@example.com") -> str:
    resp = client.post("/auth/register", json={"email": email, "password": "secret123"})
    assert resp.status_code == 201, resp.text
    return resp.json()["access_token"]


@pytest.fixture
def user_token(client: TestClient) -> str:
    return register(client)


@pytest.fixture
def admin_token(client: TestClient) -> str:
    from app.core.security import create_access_token, hash_password
    from app.database import AsyncSessionLocal
    from app.repositories.user import UserRepository

    async def _make():
        async with AsyncSessionLocal() as session:
            repo = UserRepository(session)
            user = await repo.create(email="admin@example.com", hashed_password=hash_password("secret123"), role="admin")
            return user.id
    user_id = asyncio.run(_make())
    return create_access_token(user_id)


def auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}
