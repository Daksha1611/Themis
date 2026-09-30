"""Shared GitHub API client and helpers used by every GitHub call."""

import logging

import httpx

logger = logging.getLogger(__name__)

GITHUB_API = "https://api.github.com"
_client: httpx.AsyncClient | None = None


class GitHubRetryableError(Exception):
    """GitHub asked us to back off; the caller should retry after `retry_after` seconds."""

    def __init__(self, message: str, retry_after: float) -> None:
        super().__init__(message)
        self.retry_after = retry_after


def get_client() -> httpx.AsyncClient:
    """One connection-pooled client per process, created on first use."""
    global _client
    if _client is None or _client.is_closed:
        _client = httpx.AsyncClient(base_url=GITHUB_API, timeout=15.0)
    return _client


async def close_client() -> None:
    global _client
    if _client is not None and not _client.is_closed:
        await _client.aclose()
    _client = None


def github_headers(token: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def raise_if_rate_limited(response: httpx.Response, what: str) -> None:
    """GitHub signals rate limits with 403 (and 429 for secondary limits) plus Retry-After."""
    if response.status_code in (403, 429) and "Retry-After" in response.headers:
        retry_after = float(response.headers["Retry-After"])
        logger.warning("GitHub rate limit on %s; retry after %ss", what, retry_after)
        raise GitHubRetryableError(f"rate limited on {what}", retry_after)
