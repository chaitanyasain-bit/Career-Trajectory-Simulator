"""
SQLAlchemy async session factory.

Supports two drivers:
  - asyncpg    → PostgreSQL (production)
  - aiosqlite  → SQLite in-memory (unit tests, no Postgres needed)

The correct driver is selected automatically based on DATABASE_URL prefix.

Usage (inside a FastAPI route via Depends):
    async def my_route(db: AsyncSession = Depends(get_db)):
        ...
"""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config import settings
from app.db.asyncpg_url import normalize_asyncpg_url


def _build_engine() -> AsyncEngine:
    """
    Build the async engine.

    SQLite needs connect_args check_same_thread=False and
    pool_class=StaticPool for in-memory use in tests.
    """
    url = settings.DATABASE_URL

    if url.startswith("sqlite+aiosqlite://"):
        from sqlalchemy.pool import StaticPool

        return create_async_engine(
            url,
            echo=settings.DEBUG,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
    if url.startswith("postgresql+asyncpg://"):
        database_url, connect_args = normalize_asyncpg_url(url)
        return create_async_engine(
            database_url,
            echo=settings.DEBUG,
            pool_pre_ping=True,
            pool_size=10,
            max_overflow=20,
            connect_args=connect_args,
        )
    raise ValueError(
        "DATABASE_URL must use postgresql+asyncpg or sqlite+aiosqlite."
    )


engine: AsyncEngine = _build_engine()

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Yield an async database session; auto-closes on exit."""
    async with AsyncSessionLocal() as session:
        yield session
