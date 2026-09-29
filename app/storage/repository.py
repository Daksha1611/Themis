"""Database reads and writes."""

import logging
import uuid
from typing import Any

from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

from app.storage.models import ReviewRun

logger = logging.getLogger(__name__)

# Temporary shortcut until Alembic is initialised in M2 (Open Question Q44, tech debt).
CREATE_REVIEW_RUNS_SQL = """
CREATE TABLE IF NOT EXISTS review_runs (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    repo         TEXT NOT NULL,
    pr_number    INTEGER NOT NULL,
    head_sha     TEXT NOT NULL,
    status       TEXT NOT NULL,
    started_at   TIMESTAMPTZ NOT NULL,
    completed_at TIMESTAMPTZ,
    cost_usd     NUMERIC(10, 6) DEFAULT 0,
    error        TEXT
)
"""


async def ensure_schema(engine: AsyncEngine) -> None:
    """Create the M1 tables if they do not exist. Called by the API and the worker on startup."""
    try:
        async with engine.begin() as conn:
            await conn.execute(text(CREATE_REVIEW_RUNS_SQL))
    except IntegrityError:
        # The API and worker can race to create the table on first start; the loser lands here.
        logger.info("review_runs was created concurrently by another process")


async def create_run(session: AsyncSession, run_data: dict[str, Any]) -> ReviewRun:
    run = ReviewRun(**run_data)
    session.add(run)
    await session.commit()
    await session.refresh(run)
    return run


async def update_run(
    session: AsyncSession, run_id: uuid.UUID, updates: dict[str, Any]
) -> ReviewRun:
    run = await session.get(ReviewRun, run_id)
    if run is None:
        raise LookupError(f"review run {run_id} not found")
    for field, value in updates.items():
        setattr(run, field, value)
    await session.commit()
    await session.refresh(run)
    return run
