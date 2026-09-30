"""Langfuse tracing helpers.

Tracing must never break the main flow: every helper swallows and logs its own errors, and
every helper accepts `None` so callers do not need to check whether tracing is on.

`observe()` opens an observation as the *current* OpenTelemetry context, so observations opened
inside it (in any function, across awaits) nest under it automatically. The trace's name and
its input/output are derived from its root observation, so set them there.
"""

import logging
from collections.abc import Iterator
from contextlib import AbstractContextManager, contextmanager
from functools import lru_cache
from typing import Any, Literal

from langfuse import Langfuse, propagate_attributes

from app.config import get_settings

logger = logging.getLogger(__name__)

# Langfuse v4 returns observation wrappers; typed loosely so callers do not depend on SDK internals.
Observation = Any
ObservationType = Literal["span", "generation"]


@lru_cache
def get_langfuse() -> Langfuse | None:
    settings = get_settings()
    try:
        return Langfuse(
            public_key=settings.langfuse_public_key,
            secret_key=settings.langfuse_secret_key.get_secret_value(),
            host=settings.langfuse_host,
            environment=settings.langfuse_environment,
        )
    except Exception:
        logger.warning("Langfuse client could not be initialised; tracing is off", exc_info=True)
        return None


def init_tracing() -> None:
    get_langfuse()


def shutdown_tracing() -> None:
    """Flush pending spans and stop the exporter. Call before the process exits."""
    client = get_langfuse()
    if client is None:
        return
    try:
        client.shutdown()
    except Exception:
        logger.warning("Langfuse shutdown failed", exc_info=True)


@contextmanager
def trace_attributes(
    *,
    session_id: str | None = None,
    tags: list[str] | None = None,
    metadata: dict[str, str] | None = None,
) -> Iterator[None]:
    """Trace-level attributes for every observation opened inside this block.

    Enter it *before* opening the root observation.
    """
    cm: AbstractContextManager[Any] | None = None
    try:
        cm = propagate_attributes(session_id=session_id, tags=tags, metadata=metadata)
        cm.__enter__()
    except Exception:
        logger.warning("Could not set trace attributes", exc_info=True)
        cm = None
    try:
        yield
    finally:
        if cm is not None:
            try:
                cm.__exit__(None, None, None)
            except Exception:
                logger.warning("Could not reset trace attributes", exc_info=True)


@contextmanager
def observe(
    name: str,
    *,
    as_type: ObservationType = "span",
    input: Any = None,
    metadata: dict[str, Any] | None = None,
) -> Iterator[Observation | None]:
    """Open an observation as the current context; ends it (marked ERROR on exception) on exit."""
    client = get_langfuse()
    cm: AbstractContextManager[Any] | None = None
    observation: Observation | None = None
    if client is not None:
        try:
            cm = client.start_as_current_observation(
                name=name, as_type=as_type, input=input, metadata=metadata
            )
            observation = cm.__enter__()
        except Exception:
            logger.warning("Could not start observation %s", name, exc_info=True)
            cm, observation = None, None

    try:
        yield observation
    except BaseException as exc:
        update(observation, level="ERROR", status_message=repr(exc))
        _exit(cm, exc)
        raise
    _exit(cm, None)


def update(observation: Observation | None, **fields: Any) -> None:
    """Update an observation (output, metadata, usage_details, model, level, ...)."""
    if observation is None:
        return
    try:
        observation.update(**fields)
    except Exception:
        logger.warning("Could not update observation", exc_info=True)


def _exit(cm: AbstractContextManager[Any] | None, exc: BaseException | None) -> None:
    if cm is None:
        return
    try:
        if exc is None:
            cm.__exit__(None, None, None)
        else:
            cm.__exit__(type(exc), exc, exc.__traceback__)
    except Exception:
        logger.warning("Could not end observation", exc_info=True)
