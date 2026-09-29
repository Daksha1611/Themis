"""Posting comments on pull requests."""

import logging

from app.github import auth

logger = logging.getLogger(__name__)


class GitHubRetryableError(Exception):
    """GitHub asked us to back off; the caller should retry after `retry_after` seconds."""

    def __init__(self, message: str, retry_after: float) -> None:
        super().__init__(message)
        self.retry_after = retry_after


async def post_review_comment(token: str, repo_full_name: str, pr_number: int, body: str) -> None:
    """Post a PR-level comment. M1 posts no line-level review comments."""
    async with auth.http_client() as client:
        response = await client.post(
            f"/repos/{repo_full_name}/issues/{pr_number}/comments",
            headers=auth.github_headers(token),
            json={"body": body},
        )

    # GitHub signals rate limits with 403 (and 429 for secondary limits) plus Retry-After.
    if response.status_code in (403, 429) and "Retry-After" in response.headers:
        retry_after = float(response.headers["Retry-After"])
        logger.warning(
            "GitHub rate limit posting to %s#%s; retry after %ss",
            repo_full_name,
            pr_number,
            retry_after,
        )
        raise GitHubRetryableError(f"rate limited on {repo_full_name}#{pr_number}", retry_after)

    response.raise_for_status()
