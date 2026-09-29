from types import SimpleNamespace, TracebackType
from typing import Any
from unittest.mock import AsyncMock, Mock

import pytest
from arq import Retry

from app.github.comments import GitHubRetryableError
from app.worker import job as job_module
from app.worker.job import DUMMY_COMMENT, handle_review_job

JOB = {
    "installation_id": 99,
    "repo_full_name": "octo/widgets",
    "pr_number": 7,
    "head_sha": "abc123",
    "pr_title": "Fix parser",
}


class FakeSession:
    async def __aenter__(self) -> "FakeSession":
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        return None


CTX: dict[str, Any] = {"session_factory": FakeSession}


@pytest.fixture
def mocks(monkeypatch: pytest.MonkeyPatch) -> Mock:
    manager = Mock()
    manager.get_installation_token = AsyncMock(return_value="tok-123")
    manager.post_review_comment = AsyncMock()
    manager.create_run = AsyncMock(return_value=SimpleNamespace(id="run-1"))
    for name in ("get_installation_token", "post_review_comment", "create_run"):
        monkeypatch.setattr(job_module, name, getattr(manager, name))
    return manager


async def test_calls_token_comment_and_run_in_order(mocks: Mock) -> None:
    assert await handle_review_job(CTX, JOB) == "dummy_complete"

    assert [c[0] for c in mocks.mock_calls] == [
        "get_installation_token",
        "post_review_comment",
        "create_run",
    ]
    mocks.get_installation_token.assert_awaited_once_with(99)
    mocks.post_review_comment.assert_awaited_once_with("tok-123", "octo/widgets", 7, DUMMY_COMMENT)
    run_data = mocks.create_run.await_args.args[1]
    assert run_data["status"] == "dummy"
    assert run_data["repo"] == "octo/widgets"


async def test_comment_failure_propagates(mocks: Mock) -> None:
    mocks.post_review_comment.side_effect = RuntimeError("GitHub is down")
    with pytest.raises(RuntimeError, match="GitHub is down"):
        await handle_review_job(CTX, JOB)
    mocks.create_run.assert_not_called()


async def test_rate_limit_becomes_arq_retry(mocks: Mock) -> None:
    mocks.post_review_comment.side_effect = GitHubRetryableError("rate limited", retry_after=30)
    with pytest.raises(Retry):
        await handle_review_job(CTX, JOB)
