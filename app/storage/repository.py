"""Database reads and writes."""

import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.storage.models import ReviewRun


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
