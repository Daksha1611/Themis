"""Fetching PR diffs, and working out which diff lines can take review comments."""

import logging
import re

from pydantic import BaseModel

from app.github import client as gh

logger = logging.getLogger(__name__)

# Stopgap for large PRs (Q48): chunking or file-level splitting is the real fix.
MAX_DIFF_CHARS = 100_000
_HUNK_HEADER = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@")


class PRNotFoundError(Exception):
    """GitHub returned 404 for the PR."""


class PRGoneError(Exception):
    """GitHub returned 410: the PR (or its repository) was deleted."""


class PRDiff(BaseModel):
    text: str
    original_chars: int
    truncated: bool


async def fetch_pr_diff(token: str, repo_full_name: str, pr_number: int) -> PRDiff:
    """The PR's unified diff, capped at MAX_DIFF_CHARS."""
    response = await gh.get_client().get(
        f"/repos/{repo_full_name}/pulls/{pr_number}",
        headers={**gh.github_headers(token), "Accept": "application/vnd.github.v3.diff"},
    )
    if response.status_code == 404:
        raise PRNotFoundError(f"{repo_full_name}#{pr_number} not found")
    if response.status_code == 410:
        raise PRGoneError(f"{repo_full_name}#{pr_number} is gone")
    gh.raise_if_rate_limited(response, f"diff for {repo_full_name}#{pr_number}")
    response.raise_for_status()

    text = response.text
    original_chars = len(text)
    truncated = original_chars > MAX_DIFF_CHARS
    if truncated:
        logger.warning(
            "Diff for %s#%s is %d chars; truncating to %d",
            repo_full_name,
            pr_number,
            original_chars,
            MAX_DIFF_CHARS,
        )
        text = text[:MAX_DIFF_CHARS]
    return PRDiff(text=text, original_chars=original_chars, truncated=truncated)


def commentable_lines(diff: str) -> dict[str, dict[int, int]]:
    """Map each file to the new-file line numbers visible in the diff, with their hunk index.

    GitHub only accepts review comments on these lines (added or context lines, RIGHT side).
    A multi-line comment must start and end within the same hunk.
    """
    lines_by_file: dict[str, dict[int, int]] = {}
    current: dict[int, int] | None = None
    new_line = 0
    hunk = -1
    for raw in diff.splitlines():
        if raw.startswith("+++ "):
            path = raw[4:]
            current = None
            if path.startswith("b/"):
                current = lines_by_file.setdefault(path[2:], {})
            continue
        if raw.startswith(("diff --git", "--- ", "index ", "new file", "deleted file", "rename ")):
            continue
        header = _HUNK_HEADER.match(raw)
        if header:
            new_line = int(header.group(1))
            hunk += 1
            continue
        if current is None or hunk < 0:
            continue
        if raw.startswith("+") or raw.startswith(" "):
            current[new_line] = hunk
            new_line += 1
        # "-" lines exist only on the old side; "\ No newline at end of file" is a marker.
    return lines_by_file
