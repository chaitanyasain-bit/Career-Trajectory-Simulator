import pytest_asyncio
from app.db.base import Base
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# Use an in-memory SQLite database specifically for tests to isolate them from development DB
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

@pytest_asyncio.fixture(scope="function")
async def db() -> AsyncSession:
    """Provides a fresh database session for a test function."""
    engine = create_async_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_maker = async_sessionmaker(bind=engine, expire_on_commit=False, class_=AsyncSession)

    async with session_maker() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
