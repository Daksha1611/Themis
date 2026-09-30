"""Posting Themis output on pull requests: line-level reviews and PR-level comments."""

import logging
from typing import Any

import httpx
from pydantic import BaseModel

from app.github import client as gh
from app.github.client import GitHubRetryableError
from app.github.diff import commentable_lines
from app.schemas import Finding

logger = logging.getLogger(__name__)

__all__ = ["GitHubRetryableError", "PostedReview", "post_findings", "post_review_comment"]


class PostedReview(BaseModel):
    line_comments: int
    summary_findings: int


async def post_review_comment(token: str, repo_full_name: str, pr_number: int, body: str) -> None:
    """Post a PR-level comment (used for the no-issues and error messages)."""
    response = await gh.get_client().post(
        f"/repos/{repo_full_name}/issues/{pr_number}/comments",
        headers=gh.github_headers(token),
        json={"body": body},
    )
    gh.raise_if_rate_limited(response, f"comment on {repo_full_name}#{pr_number}")
    response.raise_for_status()


def format_finding(finding: Finding) -> str:
    # raw_llm_confidence is deliberately not shown (ADR-016); it is stored and traced instead.
    return (
        f"**[{finding.severity.upper()}] {finding.category}**\n\n"
        f"{finding.message}\n\n"
        f"💡 {finding.suggestion}"
    )


def build_review(findings: list[Finding], diff: str) -> tuple[str, list[dict[str, Any]]]:
    """Split findings into line comments (on diff lines) and a summary body (everything else)."""
    visible = commentable_lines(diff)
    comments: list[dict[str, Any]] = []
    outside: list[Finding] = []
    for finding in findings:
        lines = visible.get(finding.file, {})
        if finding.line_end not in lines:
            outside.append(finding)
            continue
        comment: dict[str, Any] = {
            "path": finding.file,
            "line": finding.line_end,
            "side": "RIGHT",
            "body": format_finding(finding),
        }
        start_hunk = lines.get(finding.line_start)
        if finding.line_start < finding.line_end and start_hunk == lines[finding.line_end]:
            comment["start_line"] = finding.line_start
            comment["start_side"] = "RIGHT"
        comments.append(comment)

    body = f"⚖️ Themis found {len(findings)} potential issue(s) in this diff."
    if outside:
        body += "\n\n**Findings outside the changed lines:**"
        for finding in outside:
            body += (
                f"\n\n---\n`{finding.file}` lines {finding.line_start}–{finding.line_end}\n\n"
                + format_finding(finding)
            )
    return body, comments


async def post_findings(
    token: str,
    repo_full_name: str,
    pr_number: int,
    head_sha: str,
    findings: list[Finding],
    diff: str,
) -> PostedReview:
    """Post one PR review (event COMMENT) holding a line comment per finding on the diff."""
    body, comments = build_review(findings, diff)
    try:
        await _post_review(token, repo_full_name, pr_number, head_sha, body, comments)
        return PostedReview(
            line_comments=len(comments), summary_findings=len(findings) - len(comments)
        )
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code != 422 or not comments:
            raise
        # GitHub could not place a line comment (e.g. a path it does not recognise):
        # fall back to putting every finding in the review body.
        logger.warning("Review with line comments rejected (422); posting findings in the body")
    body, _ = build_review(findings, diff="")
    await _post_review(token, repo_full_name, pr_number, head_sha, body, [])
    return PostedReview(line_comments=0, summary_findings=len(findings))


async def _post_review(
    token: str,
    repo_full_name: str,
    pr_number: int,
    head_sha: str,
    body: str,
    comments: list[dict[str, Any]],
) -> None:
    response = await gh.get_client().post(
        f"/repos/{repo_full_name}/pulls/{pr_number}/reviews",
        headers=gh.github_headers(token),
        json={"commit_id": head_sha, "event": "COMMENT", "body": body, "comments": comments},
    )
    gh.raise_if_rate_limited(response, f"review on {repo_full_name}#{pr_number}")
    response.raise_for_status()
