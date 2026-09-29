import os

# Test configuration. Set before any app module reads settings.
os.environ.update(
    {
        "GITHUB_APP_ID": "12345",
        "GITHUB_PRIVATE_KEY": "unused-in-tests",
        "GITHUB_WEBHOOK_SECRET": "test-webhook-secret",
        "REDIS_URL": "redis://localhost:6379",
        "LANGFUSE_PUBLIC_KEY": "pk-test",
        "LANGFUSE_SECRET_KEY": "sk-test",
        "LANGFUSE_HOST": "http://127.0.0.1:9",
        # Read by the Langfuse SDK itself: no spans are exported, so no network calls.
        "LANGFUSE_TRACING_ENABLED": "false",
        "DATABASE_URL": "postgresql+psycopg://themis:themis@localhost:5432/themis",
    }
)

from collections.abc import Iterator  # noqa: E402
from unittest.mock import AsyncMock  # noqa: E402

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.api.webhook import get_queue  # noqa: E402
from app.main import create_app  # noqa: E402

WEBHOOK_SECRET = "test-webhook-secret"


@pytest.fixture
def queue() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def client(queue: AsyncMock) -> Iterator[TestClient]:
    # No `with` block: the lifespan (Postgres, Redis) is not started in unit tests.
    app = create_app()
    app.dependency_overrides[get_queue] = lambda: queue
    yield TestClient(app)
