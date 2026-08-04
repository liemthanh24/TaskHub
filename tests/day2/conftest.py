import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.database import AsyncSessionLocal, init_db
from app.models.base import Base
from app.models.user import UserModel
from app.repositories.task import TaskRepository
from app.repositories.user import UserRepository

TEST_DATABASE_URL = "sqlite+aiosqlite:///./test_taskhub.db"

@pytest.fixture(autouse=True)
async def setup_db():
    engine = create_async_engine(TEST_DATABASE_URL)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def session():
    engine = create_async_engine(TEST_DATABASE_URL)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = async_sessionmaker(engine, expire_on_commit=False)
    async with async_session() as s:
        yield s

    await engine.dispose()


@pytest_asyncio.fixture
async def user_id(session: AsyncSession) -> int:
    repo = UserRepository(session)
    user = await repo.create(email="owner@example.com", hashed_password="x")
    return user.id


@pytest_asyncio.fixture
async def repo(session: AsyncSession) -> TaskRepository:
    return TaskRepository(session)
