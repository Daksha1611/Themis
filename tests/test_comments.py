import json

import httpx
import pytest

from app.github import auth
from app.github.comments import GitHubRetryableError, post_review_comment


def mock_github(monkeypatch: pytest.MonkeyPatch, handler: httpx.MockTransport) -> None:
    monkeypatch.setattr(
        auth,
        "http_client",
        lambda: httpx.AsyncClient(base_url=auth.GITHUB_API, transport=handler),
    )


async def test_posts_to_issue_comments_endpoint(monkeypatch: pytest.MonkeyPatch) -> None:
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(201, json={"id": 1})

    mock_github(monkeypatch, httpx.MockTransport(handler))
    await post_review_comment("tok-123", "octo/widgets", 7, "hello")

    assert len(seen) == 1
    request = seen[0]
    assert request.method == "POST"
    assert str(request.url) == "https://api.github.com/repos/octo/widgets/issues/7/comments"
    assert request.headers["Authorization"] == "Bearer tok-123"
    assert request.headers["Accept"] == "application/vnd.github+json"
    assert json.loads(request.content) == {"body": "hello"}


async def test_rate_limit_raises_retryable_error(monkeypatch: pytest.MonkeyPatch) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(403, headers={"Retry-After": "30"}, json={"message": "rate limit"})

    mock_github(monkeypatch, httpx.MockTransport(handler))
    with pytest.raises(GitHubRetryableError) as excinfo:
        await post_review_comment("tok-123", "octo/widgets", 7, "hello")
    assert excinfo.value.retry_after == 30.0
