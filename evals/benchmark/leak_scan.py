"""Leak scan of the scored eval diffs (no LLM calls, changes nothing).

    python -m evals.benchmark.leak_scan --split dev

A buggy case's diff is the fix reversed, so its `-` lines are the fix's own lines, shown to the
reviewer as removed code. Comments there can name the bug ("fix for #123", "workaround for the
regression"). This scans the `-` lines of every scored case for issue or PR references and for
telltale words, and reports counts and case IDs.
"""

import argparse
import re
from collections import defaultdict
from typing import Any

from evals.benchmark.label import LABELS, load_labels
from evals.runner import scored_cases

PATTERNS: dict[str, re.Pattern[str]] = {
    "issue/PR reference (#N)": re.compile(r"(?<![\w&])#\d+\b"),
    "GitHub URL": re.compile(r"github\.com/", re.IGNORECASE),
    "fix": re.compile(r"\bfix(?:es|ed|ing)?\b", re.IGNORECASE),
    "bug": re.compile(r"\bbugs?\b", re.IGNORECASE),
    "workaround": re.compile(r"\bwork[- ]?arounds?\b", re.IGNORECASE),
    "regression": re.compile(r"\bregressions?\b", re.IGNORECASE),
    "hack": re.compile(r"\bhack(?:s|y)?\b", re.IGNORECASE),
    "see issue": re.compile(r"\bsee issue\b", re.IGNORECASE),
}


def removed_lines(diff: str) -> list[str]:
    return [
        line[1:]
        for line in diff.splitlines()
        if line.startswith("-") and not line.startswith("---")
    ]


def scan(cases: list[dict[str, Any]]) -> dict[str, dict[str, list[tuple[str, str]]]]:
    """pattern -> kind (buggy/clean) -> [(case ID, matching line)]."""
    found: dict[str, dict[str, list[tuple[str, str]]]] = defaultdict(lambda: defaultdict(list))
    for case in cases:
        for name, pattern in PATTERNS.items():
            lines = [line.strip() for line in removed_lines(case["diff"]) if pattern.search(line)]
            if lines:
                found[name][case["kind"]].append((case["case_id"], lines[0][:100]))
    return found


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--split", choices=("dev",), default="dev")
    args = parser.parse_args(argv)
    cases = scored_cases(args.split, load_labels(LABELS))
    found = scan(cases)
    total = {k: sum(c["kind"] == k for c in cases) for k in ("buggy", "clean")}
    print(f"Scored {args.split} cases: {total['buggy']} buggy, {total['clean']} clean")
    any_case: dict[str, set[str]] = defaultdict(set)
    for name in PATTERNS:
        hits = found.get(name, {})
        counts = {k: len(hits.get(k, [])) for k in ("buggy", "clean")}
        print(f"\n{name}: buggy {counts['buggy']}, clean {counts['clean']}")
        for kind in ("buggy", "clean"):
            for cid, line in hits.get(kind, []):
                any_case[kind].add(cid)
                print(f"  {kind} {cid}: {line}")
    print(
        f"\nCases with any match: buggy {len(any_case['buggy'])}/{total['buggy']}, "
        f"clean {len(any_case['clean'])}/{total['clean']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
