import logging
from collections.abc import Callable

import httpx
import pytest

from app.github.diff import (
    MAX_DIFF_CHARS,
    PRGoneError,
    PRNotFoundError,
    commentable_lines,
    fetch_pr_diff,
)
from tests.conftest import Handler


async def test_calls_pulls_endpoint_with_diff_accept_header(
    mock_github: Callable[[Handler], None],
) -> None:
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(200, text="diff --git a/x.py b/x.py\n")

    mock_github(handler)
    diff = await fetch_pr_diff("tok", "octo/widgets", 7)

    assert str(seen[0].url) == "https://api.github.com/repos/octo/widgets/pulls/7"
    assert seen[0].headers["Accept"] == "application/vnd.github.v3.diff"
    assert seen[0].headers["Authorization"] == "Bearer tok"
    assert diff.text == "diff --git a/x.py b/x.py\n" and not diff.truncated


async def test_large_diff_is_truncated_with_warning(
    mock_github: Callable[[Handler], None], caplog: pytest.LogCaptureFixture
) -> None:
    mock_github(lambda request: httpx.Response(200, text="x" * (MAX_DIFF_CHARS + 500)))
    with caplog.at_level(logging.WARNING, logger="app.github.diff"):
        diff = await fetch_pr_diff("tok", "octo/widgets", 7)

    assert len(diff.text) == MAX_DIFF_CHARS
    assert diff.truncated and diff.original_chars == MAX_DIFF_CHARS + 500
    assert "truncating" in caplog.text


async def test_404_raises_not_found(mock_github: Callable[[Handler], None]) -> None:
    mock_github(lambda request: httpx.Response(404, json={"message": "Not Found"}))
    with pytest.raises(PRNotFoundError):
        await fetch_pr_diff("tok", "octo/widgets", 7)


async def test_410_raises_gone_not_404_error(mock_github: Callable[[Handler], None]) -> None:
    mock_github(lambda request: httpx.Response(410, json={"message": "Gone"}))
    with pytest.raises(PRGoneError) as excinfo:
        await fetch_pr_diff("tok", "octo/widgets", 7)
    assert not isinstance(excinfo.value, PRNotFoundError)


def test_commentable_lines_track_new_side_line_numbers_and_hunks() -> None:
    diff = (
        "diff --git a/a.py b/a.py\n--- a/a.py\n+++ b/a.py\n"
        "@@ -1,3 +1,3 @@\n context\n-old\n+new\n context2\n"
        "@@ -20,2 +20,3 @@\n c\n+added\n c2\n"
        "diff --git a/gone.py b/gone.py\n--- a/gone.py\n+++ /dev/null\n@@ -1 +0,0 @@\n-x\n"
    )
    lines = commentable_lines(diff)
    assert lines == {"a.py": {1: 0, 2: 0, 3: 0, 20: 1, 21: 1, 22: 1}}
