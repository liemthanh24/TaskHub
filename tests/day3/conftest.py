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
