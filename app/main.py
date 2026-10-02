"""FastAPI app factory."""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api import health, webhook
from app.config import get_settings
from app.github.client import close_client
from app.observability.tracing import init_tracing, shutdown_tracing
from app.worker.queue import create_queue_client


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    logging.basicConfig(level=settings.log_level)
    # The schema is managed by Alembic: `alembic upgrade head` runs before the app starts.
    app.state.arq_pool = await create_queue_client()
    init_tracing()
    yield
    await app.state.arq_pool.aclose()
    await close_client()
    shutdown_tracing()


def create_app() -> FastAPI:
    app = FastAPI(title="Themis", lifespan=lifespan)
    app.include_router(health.router)
    app.include_router(webhook.router)
    return app


app = create_app()
