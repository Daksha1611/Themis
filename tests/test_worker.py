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
# A real hunk: findings must point at a line inside it (ADR-026 line validation).
REVIEW_DIFF = "diff --git a/a.py b/a.py\n--- a/a.py\n+++ b/a.py\n@@ -1 +1 @@\n-x = 0\n+x = 1\n"


def llm_response(content: str) -> LLMResponse:
    return LLMResponse(
        content=content,
        provider="groq",
        model="openai/gpt-oss-120b",
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
    m.fetch_pr_diff = AsyncMock(
        return_value=PRDiff(text=REVIEW_DIFF, original_chars=len(REVIEW_DIFF), truncated=False)
    )
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
    assert row["model"] == "groq/openai/gpt-oss-120b" and float(row["cost_usd"]) == 0.000228
    assert (row["diff_chars"], row["diff_truncated"]) == (len(REVIEW_DIFF), False)


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
    # both calls (the first answer and the one retry, ADR-026) cost money; both are recorded
    assert row["prompt_tokens"] == 2400 and mocks.complete.await_count == 2


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


# --- repo context (ADR-030) ---------------------------------------------------------------------


def with_budget(monkeypatch: pytest.MonkeyPatch, budget: int) -> None:
    settings = job_module.get_settings().model_copy(update={"context_budget": budget})
    monkeypatch.setattr(job_module, "get_settings", lambda: settings)


async def test_context_off_builds_nothing(mocks: Mock, monkeypatch: pytest.MonkeyPatch) -> None:
    with_budget(monkeypatch, 0)
    build = AsyncMock()
    monkeypatch.setattr("app.context.builder.build_context", build)
    assert await handle_review_job(CTX, JOB) == "success"
    build.assert_not_awaited()
    assert "<context>" not in mocks.complete.await_args.args[0][0]["content"]


async def test_context_on_adds_the_block_to_the_prompt(
    mocks: Mock, monkeypatch: pytest.MonkeyPatch
) -> None:
    from tests.test_context import chunk_context

    with_budget(monkeypatch, 1000)
    build = AsyncMock(return_value=chunk_context())
    monkeypatch.setattr("app.context.builder.build_context", build)
    assert await handle_review_job(CTX, {**JOB, "base_sha": "base1"}) == "success"
    assert build.await_args.args[:3] == ("tok-123", "octo/widgets", "base1")
    assert "<context>" in mocks.complete.await_args.args[0][0]["content"]


async def test_context_failure_reviews_the_diff_alone(
    mocks: Mock, monkeypatch: pytest.MonkeyPatch
) -> None:
    with_budget(monkeypatch, 1000)
    monkeypatch.setattr(
        "app.context.builder.build_context", AsyncMock(side_effect=RuntimeError("no tree"))
    )
    assert await handle_review_job(CTX, {**JOB, "base_sha": "base1"}) == "success"
    assert "<context>" not in mocks.complete.await_args.args[0][0]["content"]
