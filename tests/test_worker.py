import json
from types import SimpleNamespace, TracebackType
from typing import Any
from unittest.mock import AsyncMock, Mock

import pytest
from arq import Retry

from app.github.client import GitHubRetryableError
from app.github.comments import PostedReview
from app.github.diff import PRDiff
from app.llm import LLMResponse
from app.worker import job as job_module
from app.worker.job import ERROR_COMMENT, NO_ISSUES_COMMENT, handle_review_job

JOB = {
    "installation_id": 99,
    "repo_full_name": "octo/widgets",
    "pr_number": 7,
    "head_sha": "abc123",
    "pr_title": "Fix parser",
}
FINDING = {
    "file": "a.py",
    "line_start": 1,
    "line_end": 1,
    "category": "error-handling",
    "severity": "medium",
    "message": "Exception is swallowed.",
    "suggestion": "Re-raise or log it.",
    "raw_llm_confidence": 0.7,
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


def llm_response(content: str) -> LLMResponse:
    return LLMResponse(
        content=content,
        model="openai/gpt-4o-mini",
        prompt_tokens=1200,
        completion_tokens=80,
        total_tokens=1280,
        cost_usd=0.000228,
    )


@pytest.fixture
def mocks(monkeypatch: pytest.MonkeyPatch) -> Mock:
    """Mocks every external call; `mocks.mock_calls` records their order."""
    m = Mock()
    m.get_installation_token = AsyncMock(return_value="tok-123")
    m.fetch_pr_diff = AsyncMock(return_value=PRDiff(text="diff", original_chars=4, truncated=False))
    m.complete = AsyncMock(return_value=llm_response(json.dumps([FINDING, FINDING])))
    m.post_findings = AsyncMock(return_value=PostedReview(line_comments=2, summary_findings=0))
    m.post_review_comment = AsyncMock()
    m.create_run = AsyncMock(return_value=SimpleNamespace(id="run-1"))
    for name in (
        "get_installation_token",
        "fetch_pr_diff",
        "post_findings",
        "post_review_comment",
        "create_run",
    ):
        monkeypatch.setattr(job_module, name, getattr(m, name))
    monkeypatch.setattr("app.graph.baseline.complete", m.complete)
    return m


def call_order(m: Mock) -> list[str]:
    return [c[0] for c in m.mock_calls if not c[0].endswith("__")]


async def test_full_flow_in_order(mocks: Mock) -> None:
    assert await handle_review_job(CTX, JOB) == "success"

    assert call_order(mocks) == [
        "get_installation_token",
        "fetch_pr_diff",
        "complete",
        "post_findings",
        "create_run",
    ]
    findings = mocks.post_findings.await_args.args[4]
    assert len(findings) == 2
    row = mocks.create_run.await_args.args[1]
    assert row["status"] == "success"
    assert (row["finding_count"], row["raw_finding_count"]) == (2, 2)
    assert (row["prompt_tokens"], row["completion_tokens"]) == (1200, 80)
    assert row["model"] == "openai/gpt-4o-mini" and float(row["cost_usd"]) == 0.000228
    assert (row["diff_chars"], row["diff_truncated"]) == (4, False)


async def test_no_findings_posts_no_issues_comment(mocks: Mock) -> None:
    mocks.complete.return_value = llm_response("[]")
    assert await handle_review_job(CTX, JOB) == "success"
    mocks.post_review_comment.assert_awaited_once_with(
        "tok-123", "octo/widgets", 7, NO_ISSUES_COMMENT
    )
    mocks.post_findings.assert_not_called()


async def test_failed_parse_posts_error_comment_and_records_failed_run(mocks: Mock) -> None:
    mocks.complete.return_value = llm_response("not json at all")
    assert await handle_review_job(CTX, JOB) == "failed"

    mocks.post_review_comment.assert_awaited_once_with("tok-123", "octo/widgets", 7, ERROR_COMMENT)
    mocks.post_findings.assert_not_called()
    row = mocks.create_run.await_args.args[1]
    assert row["status"] == "failed" and "baseline review failed" in row["error"]
    assert row["prompt_tokens"] == 1200  # the LLM call still cost money; it is recorded


async def test_diff_fetch_failure_posts_error_comment_and_records_failed_run(mocks: Mock) -> None:
    mocks.fetch_pr_diff.side_effect = RuntimeError("GitHub is down")
    assert await handle_review_job(CTX, JOB) == "failed"

    mocks.complete.assert_not_called()
    mocks.post_review_comment.assert_awaited_once_with("tok-123", "octo/widgets", 7, ERROR_COMMENT)
    row = mocks.create_run.await_args.args[1]
    assert row["status"] == "failed" and "diff fetch failed" in row["error"]


async def test_rate_limit_becomes_arq_retry(mocks: Mock) -> None:
    mocks.post_findings.side_effect = GitHubRetryableError("rate limited", retry_after=30)
    with pytest.raises(Retry):
        await handle_review_job(CTX, JOB)


async def test_auth_failure_records_run_and_propagates(mocks: Mock) -> None:
    mocks.get_installation_token.side_effect = RuntimeError("bad key")
    with pytest.raises(RuntimeError, match="bad key"):
        await handle_review_job(CTX, JOB)
    assert mocks.create_run.await_args.args[1]["status"] == "failed"
