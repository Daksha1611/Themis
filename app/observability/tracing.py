"""Langfuse tracing helpers.

Tracing must never break the main flow: every helper swallows and logs its own errors,
and every helper accepts `None` so callers do not need to check whether tracing is on.
"""

import logging
from functools import lru_cache
from typing import Any

from langfuse import Langfuse

from app.config import get_settings

logger = logging.getLogger(__name__)

# Langfuse v4 returns observation wrappers from start_observation(); typed loosely on purpose
# so callers do not depend on SDK internals.
Observation = Any


@lru_cache
def get_langfuse() -> Langfuse | None:
    settings = get_settings()
    try:
        return Langfuse(
            public_key=settings.langfuse_public_key,
            secret_key=settings.langfuse_secret_key.get_secret_value(),
            host=settings.langfuse_host,
        )
    except Exception:
        logger.warning("Langfuse client could not be initialised; tracing is off", exc_info=True)
        return None


def init_tracing() -> None:
    get_langfuse()


def shutdown_tracing() -> None:
    client = get_langfuse()
    if client is None:
        return
    try:
        client.shutdown()
    except Exception:
        logger.warning("Langfuse shutdown failed", exc_info=True)


def start_trace(name: str, metadata: dict[str, Any]) -> Observation | None:
    """Start a root observation, which creates a new Langfuse trace."""
    client = get_langfuse()
    if client is None:
        return None
    try:
        return client.start_observation(name=name, metadata=metadata)
    except Exception:
        logger.warning("Could not start trace %s", name, exc_info=True)
        return None


def update_trace(trace: Observation | None, metadata: dict[str, Any]) -> None:
    if trace is None:
        return
    try:
        trace.update(metadata=metadata)
    except Exception:
        logger.warning("Could not update trace metadata", exc_info=True)


def end_trace(trace: Observation | None, output: Any, error: BaseException | None = None) -> None:
    _end(trace, output, error)


def start_span(trace: Observation | None, name: str, input: Any) -> Observation | None:
    if trace is None:
        return None
    try:
        return trace.start_observation(name=name, input=input)
    except Exception:
        logger.warning("Could not start span %s", name, exc_info=True)
        return None


def end_span(span: Observation | None, output: Any, error: BaseException | None = None) -> None:
    _end(span, output, error)


def _end(observation: Observation | None, output: Any, error: BaseException | None) -> None:
    if observation is None:
        return
    try:
        if error is None:
            observation.update(output=output)
        else:
            observation.update(output=output, level="ERROR", status_message=repr(error))
        observation.end()
    except Exception:
        logger.warning("Could not end observation", exc_info=True)
