import json
from collections.abc import Callable

import httpx
import pytest

from app.github.comments import (
    GitHubRetryableError,
    build_review,
    post_findings,
    post_review_comment,
)
from app.schemas import Finding
from tests.conftest import Handler

DIFF = """diff --git a/app/calc.py b/app/calc.py
index 111..222 100644
--- a/app/calc.py
+++ b/app/calc.py
@@ -10,3 +10,5 @@ def total(items):
     result = 0
-    for i in range(len(items)):
+    for i in range(len(items) + 1):
+        result += items[i]
     return result
"""


def finding(line_start: int, line_end: int, file: str = "app/calc.py") -> Finding:
    return Finding(
        file=file,
        line_start=line_start,
        line_end=line_end,
        category="off-by-one-or-boundary",
        severity="high",
        message="Loop reads past the end of the list.",
        suggestion="Iterate over range(len(items)).",
        raw_llm_confidence=0.9,
    )


async def test_posts_to_issue_comments_endpoint(mock_github: Callable[[Handler], None]) -> None:
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(201, json={"id": 1})

    mock_github(handler)
    await post_review_comment("tok-123", "octo/widgets", 7, "hello")

    assert len(seen) == 1
    request = seen[0]
    assert request.method == "POST"
    assert str(request.url) == "https://api.github.com/repos/octo/widgets/issues/7/comments"
    assert request.headers["Authorization"] == "Bearer tok-123"
    assert request.headers["Accept"] == "application/vnd.github+json"
    assert json.loads(request.content) == {"body": "hello"}


async def test_rate_limit_raises_retryable_error(mock_github: Callable[[Handler], None]) -> None:
    mock_github(lambda request: httpx.Response(403, headers={"Retry-After": "30"}, json={}))
    with pytest.raises(GitHubRetryableError) as excinfo:
        await post_review_comment("tok-123", "octo/widgets", 7, "hello")
    assert excinfo.value.retry_after == 30.0


def test_findings_on_diff_lines_become_line_comments() -> None:
    body, comments = build_review([finding(11, 12)], DIFF)
    assert comments == [
        {
            "path": "app/calc.py",
            "line": 12,
            "side": "RIGHT",
            "body": comments[0]["body"],
            "start_line": 11,
            "start_side": "RIGHT",
        }
    ]
    assert "[HIGH] off-by-one-or-boundary" in comments[0]["body"]
    assert "Confidence" not in comments[0]["body"]  # raw LLM confidence is never shown (ADR-016)
    assert "outside the changed lines" not in body


def test_findings_outside_the_diff_go_in_the_summary() -> None:
    body, comments = build_review([finding(40, 41), finding(3, 3, file="other.py")], DIFF)
    assert comments == []
    assert "Findings outside the changed lines" in body
    assert "`app/calc.py` lines 40–41" in body
    assert "`other.py` lines 3–3" in body


async def test_post_findings_sends_one_review_with_line_comments(
    mock_github: Callable[[Handler], None],
) -> None:
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(200, json={"id": 5})

    mock_github(handler)
    posted = await post_findings("tok", "octo/widgets", 7, "abc123", [finding(12, 12)], DIFF)

    assert posted.line_comments == 1 and posted.summary_findings == 0
    assert str(seen[0].url) == "https://api.github.com/repos/octo/widgets/pulls/7/reviews"
    payload = json.loads(seen[0].content)
    assert payload["event"] == "COMMENT" and payload["commit_id"] == "abc123"
    assert payload["comments"][0]["line"] == 12


async def test_post_findings_falls_back_to_body_on_422(
    mock_github: Callable[[Handler], None],
) -> None:
    payloads: list[dict[str, object]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        payload = json.loads(request.content)
        payloads.append(payload)
        return httpx.Response(422 if payload["comments"] else 200, json={})

    mock_github(handler)
    posted = await post_findings("tok", "octo/widgets", 7, "abc123", [finding(12, 12)], DIFF)

    assert len(payloads) == 2 and payloads[1]["comments"] == []
    assert posted.line_comments == 0 and posted.summary_findings == 1
