"""Retrieve related code for a diff (M4, not yet wired into the review path).

One hybrid query per hunk: the hunk header's enclosing-scope text plus the hunk's changed lines.
Chunks overlapping the diff's own changed region (same file, old-side line range of a hunk) are
skipped: the diff already shows them (ADR-027). Remaining chunks are ranked by their best RRF
score across hunks and added greedily until the token budget is spent.
"""

import re
from collections.abc import Callable

from pydantic import BaseModel

from app.context.chunker import Chunk
from app.context.index import HybridIndex

HUNK = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+\d+(?:,\d+)? @@(.*)$")


class RelatedChunk(BaseModel):
    """One `ReviewContext.related_chunks` entry ([[Finding Schema]])."""

    path: str
    symbol: str
    code: str
    score: float
    reason: str
    start_line: int
    end_line: int
    tokens: int


class RetrievedContext(BaseModel):
    related_chunks: list[RelatedChunk]
    token_budget: int
    token_budget_used: int


def count_tokens(text: str) -> int:
    from litellm import token_counter  # noqa: PLC0415 (heavy import)

    return int(token_counter(model="gpt-4o", text=text))


def hunks(diff: str) -> list[tuple[str, int, int, str]]:
    """(path, old-side start, old-side end, query text) per hunk."""
    out: list[tuple[str, int, int, str]] = []
    path: str | None = None
    current: list[str] = []
    start = end = 0
    scope = ""

    def flush() -> None:
        if path is not None and current:
            out.append((path, start, end, "\n".join([scope, *current]).strip()))

    for raw in diff.splitlines():
        if raw.startswith("+++ "):
            flush()
            current = []
            path = raw[6:] if raw.startswith("+++ b/") else None
            continue
        if raw.startswith(("diff --git", "--- ", "index ")):
            continue
        if match := HUNK.match(raw):
            flush()
            current = []
            start = int(match.group(1))
            count = int(match.group(2)) if match.group(2) is not None else 1
            end = start + max(count, 1) - 1
            scope = match.group(3).strip()
            continue
        if raw.startswith(("+", "-")):
            current.append(raw[1:])
    flush()
    return out


def retrieve(
    index: HybridIndex,
    diff: str,
    budget: int,
    per_hunk: int = 20,
    count: Callable[[str], int] = count_tokens,
) -> RetrievedContext:
    regions = hunks(diff)
    best: dict[tuple[str, str, int], tuple[Chunk, float, str]] = {}
    for number, (path, _start, _end, query) in enumerate(regions, 1):
        for chunk, score in index.search(query, per_hunk):
            if any(
                chunk.path == p and chunk.start_line <= e and chunk.end_line >= s
                for p, s, e, _ in regions
            ):
                continue  # inside the diff's own changed region
            key = (chunk.path, chunk.symbol, chunk.start_line)
            if key not in best or score > best[key][1]:
                best[key] = (chunk, score, f"hybrid match to hunk {number} of {path}")
    selected: list[RelatedChunk] = []
    used = 0
    for chunk, score, reason in sorted(best.values(), key=lambda x: -x[1]):
        tokens = count(chunk.code)
        if used + tokens > budget:
            continue
        used += tokens
        selected.append(
            RelatedChunk(
                path=chunk.path,
                symbol=chunk.symbol,
                code=chunk.code,
                score=score,
                reason=reason,
                start_line=chunk.start_line,
                end_line=chunk.end_line,
                tokens=tokens,
            )
        )
    return RetrievedContext(related_chunks=selected, token_budget=budget, token_budget_used=used)
