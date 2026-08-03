import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.security import hash_password
from app.models.base import Base
from app.models.user import UserModel
from app.repositories.user import UserRepository

TEST_DATABASE_URL = "sqlite+aiosqlite:///./test_users.db"


@pytest_asyncio.fixture
async def repo():
    engine = create_async_engine(TEST_DATABASE_URL)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    async_session = async_sessionmaker(engine, expire_on_commit=False)
    async with async_session() as session:
        yield UserRepository(session)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.mark.asyncio
async def test_create_user_hashes_password(repo):
    user = await repo.create(email="user@example.com", hashed_password=hash_password("secret123"))
    assert user.id >= 1
    assert user.email == "user@example.com"
    assert user.hashed_password != "secret123"
    assert user.is_active is True


@pytest.mark.asyncio
async def test_get_by_email_found(repo):
    await repo.create(email="find@example.com", hashed_password=hash_password("secret123"))
    user = await repo.get_by_email("find@example.com")
    assert user is not None
    assert user.email == "find@example.com"


@pytest.mark.asyncio
async def test_get_by_email_not_found(repo):
    assert await repo.get_by_email("missing@example.com") is None


@pytest.mark.asyncio
async def test_get_by_email_case_sensitive(repo):
    await repo.create(email="case@example.com", hashed_password=hash_password("secret123"))
    assert await repo.get_by_email("CASE@example.com") is None
