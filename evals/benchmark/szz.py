"""SZZ-style attribution for clean-case selection (Q60).

The SZZ algorithm (Śliwerski, Zimmermann and Zeller, "When do changes induce fixes?", MSR 2005)
finds the commits that introduced a bug by running `git blame` on the lines a bug-fix commit
removes or modifies, at the fix's parent. A commit blamed by a later fix touched lines that
needed fixing, so it is not a clean case.
"""

import re
from pathlib import Path

from evals.benchmark.verify_repos import git

HUNK = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@")
SHA_LINE = re.compile(r"^([0-9a-f]{40}) \d+ \d+")


def removed_ranges(diff: str) -> dict[str, list[tuple[int, int]]]:
    """Old-side line ranges of removed lines, per file, from a `-U0` diff."""
    ranges: dict[str, list[tuple[int, int]]] = {}
    path: str | None = None
    for line in diff.splitlines():
        if line.startswith("--- "):
            target = line[4:]
            path = target[2:] if target.startswith("a/") else None
            continue
        match = HUNK.match(line)
        if match and path is not None:
            start, count = int(match.group(1)), int(match.group(2) or "1")
            if count > 0:  # count 0: a pure addition, nothing to blame
                ranges.setdefault(path, []).append((start, start + count - 1))
    return ranges


def added_lines(diff: str) -> dict[str, set[int]]:
    """New-side line numbers of added or modified lines, per file."""
    lines: dict[str, set[int]] = {}
    path: str | None = None
    new_line = 0
    for raw in diff.splitlines():
        if raw.startswith("+++ "):
            target = raw[4:]
            path = target[2:] if target.startswith("b/") else None
            continue
        if raw.startswith(("diff --git", "--- ", "index ")):
            continue
        match = HUNK.match(raw)
        if match:
            new_line = int(match.group(3))
            continue
        if raw.startswith("+") and path is not None:
            lines.setdefault(path, set()).add(new_line)
            new_line += 1
        elif raw.startswith(" "):
            new_line += 1
    return lines


def blamed_commits(repo_dir: Path, fix: str, parent: str, files: list[str]) -> set[str]:
    """Commits that last touched the lines `fix` removes or modifies (blame at its parent)."""
    diff = git(repo_dir, "diff", "--no-color", "-U0", parent, fix, "--", *files)
    blamed: set[str] = set()
    for path, ranges in removed_ranges(diff).items():
        args = [arg for start, end in ranges for arg in ("-L", f"{start},{end}")]
        out = git(repo_dir, "blame", "--porcelain", "-w", *args, parent, "--", path)
        blamed |= {m.group(1) for m in map(SHA_LINE.match, out.splitlines()) if m}
    return blamed
