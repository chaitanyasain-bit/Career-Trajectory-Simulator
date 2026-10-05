"""
Database health check utilities.

check_db_connection() is called by the /health endpoint to verify
the database is reachable. Returns a dict with status and detail.
"""

from __future__ import annotations

import logging
from typing import Any

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.db.session import engine

logger = logging.getLogger(__name__)


async def check_db_connection() -> dict[str, Any]:
    """
    Execute a trivial SQL statement to confirm the DB is reachable.

    Returns
    -------
    {"status": "ok" | "error", "detail": str | None}
    """
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return {"status": "ok", "detail": None}
    except SQLAlchemyError as exc:
        logger.warning("Database health check failed: %s", exc)
        return {"status": "error", "detail": str(exc)}
    except Exception as exc:  # noqa: BLE001
        logger.error("Unexpected error during DB health check: %s", exc)
        return {"status": "error", "detail": "unexpected error"}
