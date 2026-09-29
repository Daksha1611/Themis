"""arq worker settings, and the queue client the API uses to enqueue jobs."""

import logging
from typing import Any

from arq import create_pool
from arq.connections import ArqRedis, RedisSettings
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.config import get_settings
from app.observability.tracing import init_tracing, shutdown_tracing
from app.storage.repository import ensure_schema
from app.worker.job import handle_review_job

REVIEW_JOB = "handle_review_job"


def redis_settings() -> RedisSettings:
    return RedisSettings.from_dsn(get_settings().redis_url)


async def create_queue_client() -> ArqRedis:
    return await create_pool(redis_settings())


async def startup(ctx: dict[str, Any]) -> None:
    logging.basicConfig(level=get_settings().log_level)
    engine = create_async_engine(get_settings().database_url)
    await ensure_schema(engine)
    ctx["engine"] = engine
    ctx["session_factory"] = async_sessionmaker(engine, expire_on_commit=False)
    init_tracing()


async def shutdown(ctx: dict[str, Any]) -> None:
    await ctx["engine"].dispose()
    shutdown_tracing()


class WorkerSettings:
    functions = [handle_review_job]
    on_startup = startup
    on_shutdown = shutdown
    redis_settings = redis_settings()
    max_tries = 5
