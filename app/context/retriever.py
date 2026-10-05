"""Retrieve related code for a diff (M4, not yet wired into the review path).

The token budget is filled in priority order (ADR-028):
1. definitions of names referenced in the changed lines (structural lookup, `PackageIndex`);
2. callers of functions whose body the diff changes;
3. hybrid semantic search: one query per hunk (scope text plus changed lines), ranked by best
   RRF score (ADR-015).
Chunks overlapping the diff's own changed region (same file, old-side line range of a hunk) are
skipped: the diff already shows them (ADR-027). Each chunk records its source and, for structural
chunks, the name that led to it.
"""

import re
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Literal

from pydantic import BaseModel

from app.context.chunker import Chunk, parse
from app.context.index import HybridIndex
from app.context.structure import PackageIndex, Reference, Resolution, references

Source = Literal["definition", "caller", "semantic"]
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
    source: Source = "semantic"
    via: str | None = None  # the referenced or changed name behind a structural chunk
    ambiguous: bool = False


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


@dataclass
class Change:
    path: str
    old_start: int
    old_end: int
    removed: set[int]  # old-side line numbers of removed lines
    added: list[str]  # text of added lines


def changes(diff: str) -> list[Change]:
    out: list[Change] = []
    path: str | None = None
    old = 0
    for raw in diff.splitlines():
        if raw.startswith("+++ "):
            path = raw[6:] if raw.startswith("+++ b/") else None
            continue
        if raw.startswith(("diff --git", "--- ", "index ")):
            continue
        if match := HUNK.match(raw):
            old = int(match.group(1))
            count = int(match.group(2)) if match.group(2) is not None else 1
            if path is not None:
                out.append(Change(path, old, old + max(count, 1) - 1, set(), []))
            continue
        if not out or path is None:
            continue
        if raw.startswith("-"):
            out[-1].removed.add(old)
            old += 1
        elif raw.startswith("+"):
            out[-1].added.append(raw[1:])
        elif raw.startswith(" "):
            old += 1
    return out


@dataclass
class Structural:
    definitions: list[tuple[Chunk, str, bool]] = field(default_factory=list)  # chunk, via, ambig.
    callers: list[tuple[Chunk, str, bool]] = field(default_factory=list)
    resolutions: list[tuple[str, Reference, Resolution]] = field(default_factory=list)
    changed_functions: list[Chunk] = field(default_factory=list)


def _dedent(lines: list[str]) -> str:
    indents = [len(x) - len(x.lstrip()) for x in lines if x.strip()]
    cut = min(indents) if indents else 0
    return "\n".join(x[cut:] for x in lines)


def structural(structure: PackageIndex, diff: str) -> Structural:
    """Definitions of names referenced on changed lines, and callers of changed functions."""
    found = Structural()
    for change in changes(diff):
        if change.path not in structure.trees:
            continue
        modules = {a for a, (_, n) in structure.imports.get(change.path, {}).items() if n is None}
        refs = references(structure.trees[change.path], change.removed, modules)
        if change.added:
            refs += references(parse(_dedent(change.added).encode()), None, modules)
        anchor = min(change.removed) if change.removed else change.old_start
        for ref in refs:
            resolution = structure.resolve(change.path, anchor, ref)
            found.resolutions.append((change.path, ref, resolution))
            for chunk in resolution.chunks:
                found.definitions.append((chunk, ref.name, resolution.ambiguous))
        lines = change.removed or {change.old_start}
        for chunk in structure.chunks.get(change.path, []):
            if chunk.kind in ("function", "method") and any(
                chunk.start_line <= n <= chunk.end_line for n in lines
            ):
                found.changed_functions.append(chunk)
    for function in found.changed_functions:
        name = function.symbol.rsplit(".", 1)[-1]
        defined = len(structure.methods_by_name.get(name, [])) + sum(
            name in defs for defs in structure.top.values()
        )
        for path, line in structure.call_sites(name):
            caller = structure.enclosing_chunk(path, line)
            if caller is not None and caller != function:
                found.callers.append((caller, name, defined > 1))
    return found


def retrieve(
    index: HybridIndex,
    diff: str,
    budget: int,
    per_hunk: int = 20,
    count: Callable[[str], int] = count_tokens,
    structure: PackageIndex | None = None,
) -> RetrievedContext:
    regions = hunks(diff)

    def in_diff(chunk: Chunk) -> bool:
        return any(
            chunk.path == p and chunk.start_line <= e and chunk.end_line >= s
            for p, s, e, _ in regions
        )

    candidates: list[tuple[Chunk, float, str, Source, str | None, bool]] = []
    if structure is not None:
        found = structural(structure, diff)
        for chunk, via, ambiguous in found.definitions:
            reason = f"definition of `{via}` referenced in the diff"
            candidates.append((chunk, 1.0, reason, "definition", via, ambiguous))
        for chunk, via, ambiguous in found.callers:
            reason = f"calls `{via}`, which the diff changes"
            candidates.append((chunk, 1.0, reason, "caller", via, ambiguous))
    best: dict[tuple[str, str, int], tuple[Chunk, float, str]] = {}
    for number, (path, _start, _end, query) in enumerate(regions, 1):
        for chunk, score in index.search(query, per_hunk):
            key = (chunk.path, chunk.symbol, chunk.start_line)
            if key not in best or score > best[key][1]:
                best[key] = (chunk, score, f"hybrid match to hunk {number} of {path}")
    for chunk, score, reason in sorted(best.values(), key=lambda x: -x[1]):
        candidates.append((chunk, score, reason, "semantic", None, False))

    selected: list[RelatedChunk] = []
    taken: set[tuple[str, str, int]] = set()
    used = 0
    for chunk, score, reason, source, via_name, is_ambiguous in candidates:
        key = (chunk.path, chunk.symbol, chunk.start_line)
        if key in taken or in_diff(chunk):
            continue  # already included, or inside the diff's own changed region
        tokens = count(chunk.code)
        if used + tokens > budget:
            continue
        taken.add(key)
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
                source=source,
                via=via_name,
                ambiguous=is_ambiguous,
            )
        )
    return RetrievedContext(related_chunks=selected, token_budget=budget, token_budget_used=used)
