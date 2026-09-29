"""FastAPI app factory."""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy.ext.asyncio import create_async_engine

from app.api import health, webhook
from app.config import get_settings
from app.observability.tracing import init_tracing, shutdown_tracing
from app.storage.repository import ensure_schema
from app.worker.queue import create_queue_client


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    logging.basicConfig(level=settings.log_level)
    engine = create_async_engine(settings.database_url)
    await ensure_schema(engine)
    app.state.arq_pool = await create_queue_client()
    init_tracing()
    yield
    await app.state.arq_pool.aclose()
    await engine.dispose()
    shutdown_tracing()


def create_app() -> FastAPI:
    app = FastAPI(title="Themis", lifespan=lifespan)
    app.include_router(health.router)
    app.include_router(webhook.router)
    return app


app = create_app()
