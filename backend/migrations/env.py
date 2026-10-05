"""
Alembic migration environment — async version for SQLAlchemy 2.x + asyncpg.

Key behaviour:
- DATABASE_URL is read from the environment (via app.config.settings),
  never from alembic.ini — so no credentials in source control.
- All ORM models are imported via app.models so autogenerate can diff them.
- run_migrations_online() uses async_engine_from_config for asyncpg support.
"""

import asyncio
import os

# ── Load our application config to get DATABASE_URL ──────────────────────────
import sys
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

# Ensure the backend/ directory is on sys.path so 'app' imports resolve
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# ── Import all models so Alembic can discover every table ────────────────────
import app.models  # noqa: F401, E402  — side-effect: registers all mappers
from app.config import settings  # noqa: E402
from app.db.asyncpg_url import normalize_asyncpg_url  # noqa: E402
from app.db.base import Base  # noqa: E402

# ── Alembic config ───────────────────────────────────────────────────────────
config = context.config

# Interpret the config file for Python logging (if present)
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Override the URL from our settings so credentials come from .env
database_url, connect_args = normalize_asyncpg_url(settings.DATABASE_URL)
rendered_url = database_url.render_as_string(hide_password=False).replace("%", "%%")
config.set_main_option("sqlalchemy.url", rendered_url)

target_metadata = Base.metadata


# ---------------------------------------------------------------------------
# Offline migrations (no live DB connection)
# ---------------------------------------------------------------------------

def run_migrations_offline() -> None:
    """
    Run migrations without an actual DB connection.
    Generates raw SQL that can be inspected or applied manually.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


# ---------------------------------------------------------------------------
# Online migrations (connects to live DB)
# ---------------------------------------------------------------------------

def do_run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        compare_server_default=True,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Create an async engine and run migrations within a synchronous wrapper."""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        connect_args=connect_args,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Entry point for online migration (used by `alembic upgrade head`)."""
    asyncio.run(run_async_migrations())


# ---------------------------------------------------------------------------
# Dispatch
# ---------------------------------------------------------------------------

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
