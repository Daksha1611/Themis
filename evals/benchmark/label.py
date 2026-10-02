"""Human labelling of benchmark cases (Q61). Resumable, one case at a time, no LLM calls.

    python -m evals.benchmark.label --split dev

Every answer is one short key plus Enter; Enter alone accepts the default shown in brackets.
Labels are appended to evals/benchmark/data/labels_human.jsonl after every case (the last record
for a case wins), so the tool can stop at any point and resume where it left off.

The holdout split is labelled only after prompt tuning is frozen: `--split holdout` is refused
unless `--freeze` is passed.
"""

import argparse
import json
import re
import sys
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from app.taxonomy import LOGIC_CATEGORIES, PRECEDENCE_RULES, SECURITY_CATEGORIES, SECURITY_OTHER

DATA = Path("evals/benchmark/data")
LABELS = DATA / "labels_human.jsonl"
CATEGORIES = [*LOGIC_CATEGORIES, *SECURITY_CATEGORIES, SECURITY_OTHER]
DROP_REASONS = {
    "f": "feature",
    "t": "typing-only",
    "r": "refactor",
    "n": "not-a-bug",
    "o": "other",
}
HUNK = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@")

Ask = Callable[[str], str]
Say = Callable[[str], None]


class Back(Exception):
    """Go back one case."""


class Quit(Exception):
    """Stop; progress so far is saved."""


def paint(text: str, code: str, color: bool) -> str:
    return f"\033[{code}m{text}\033[0m" if color else text


def numbered_diff(diff: str, labels: list[dict[str, Any]], color: bool = True) -> str:
    """The diff the reviewer sees, coloured, with each labelled range's lines marked [k]."""
    out = []
    path: str | None = None
    new_line = 0
    for raw in diff.splitlines():
        marker = "    "
        if raw.startswith("+++ "):
            path = raw[6:] if raw.startswith("+++ b/") else None
        elif header := HUNK.match(raw):
            new_line = int(header.group(1))
        elif raw.startswith(("+", " ")) and not raw.startswith("+++"):
            hits = [
                str(k)
                for k, span in enumerate(labels, 1)
                if span["file"] == path and span["line_start"] <= new_line <= span["line_end"]
            ]
            if hits:
                marker = f"[{','.join(hits)}]".ljust(4)
            new_line += 1
        if raw.startswith("+") and not raw.startswith("+++"):
            line = paint(raw, "32", color)
        elif raw.startswith("-") and not raw.startswith("---"):
            line = paint(raw, "31", color)
        elif raw.startswith("@@"):
            line = paint(raw, "36", color)
        elif raw.startswith(("diff --git", "+++", "---", "index")):
            line = paint(raw, "1", color)
        else:
            line = raw
        out.append(paint(marker, "33;1", color) + line)
    return "\n".join(out)


def render(case: dict[str, Any], index: int, total: int, color: bool = True) -> str:
    spans = case["labels"]
    lines = [
        "",
        paint(
            f"═══ Case {index}/{total} · {case['case_id']} · {case['kind'].upper()} · "
            f"{case['repo']} ═══",
            "1",
            color,
        ),
        f"Commit:  {case['url']}  ({case['date']})",
        f"Issue:   {case.get('linked_issue') or '—'}   PR: {case.get('pr_ref') or '—'}",
    ]
    if case["kind"] == "buggy":
        lines.append(
            f"Heuristic category: {case['category_label'] or 'none'} ({case['category_reason']})"
        )
        lines.append("Labelled ranges:")
        lines += [
            f"  [{k}] {s['file']} lines {s['line_start']}–{s['line_end']}"
            for k, s in enumerate(spans, 1)
        ]
    lines += [
        "",
        "Original commit message:",
        *("  " + m for m in case["message"].splitlines()),
        "",
        "Diff the reviewer sees" + (" (the fix reversed):" if case["kind"] == "buggy" else ":"),
        numbered_diff(case["diff"], spans, color),
    ]
    return "\n".join(lines)


def category_help() -> str:
    listing = "  ".join(f"{i}={c}" for i, c in enumerate(CATEGORIES, 1))
    rules = "\n".join(f"  - {r}" for r in PRECEDENCE_RULES)
    return f"Categories: {listing}\nWhen two could apply:\n{rules}"


def prompt(ask: Ask, say: Say, question: str, valid: Callable[[str], bool]) -> str:
    """Ask until the answer is valid. `b` goes back one case, `q` quits."""
    while True:
        answer = ask(question).strip()
        if answer == "b":
            raise Back
        if answer == "q":
            raise Quit
        if valid(answer):
            return answer
        say("  ? not understood; try again (b = back, q = quit)")


def label_buggy(case: dict[str, Any], ask: Ask, say: Say) -> dict[str, Any]:
    reasons = " ".join(f"[{k}]{v}" for k, v in DROP_REASONS.items())
    valid = prompt(
        ask,
        say,
        f"Valid bug fix? [y]es (Enter) or drop: {reasons} > ",
        lambda a: a in ("", "y", *DROP_REASONS),
    )
    if valid not in ("", "y"):
        note = ask("  Note (optional) > ").strip()
        return {"valid": False, "drop_reason": DROP_REASONS[valid], "note": note}

    default = case["category_label"]
    say(category_help())
    hint = f"Enter = {default}" if default else "no default"
    raw = prompt(
        ask,
        say,
        f"Category number ({hint}) > ",
        lambda a: (
            (a == "" and default is not None) or (a.isdigit() and 1 <= int(a) <= len(CATEGORIES))
        ),
    )
    category = default if raw == "" else CATEGORIES[int(raw) - 1]
    subcategory = None
    if category == SECURITY_OTHER:
        subcategory = prompt(ask, say, "  Subcategory (short name) > ", bool)

    spans = case["labels"]
    if len(spans) == 1:
        primary = 1
    else:
        raw = prompt(
            ask,
            say,
            f"Primary range, the actual bug [1-{len(spans)}] (Enter = 1) > ",
            lambda a: a == "" or (a.isdigit() and 1 <= int(a) <= len(spans)),
        )
        primary = int(raw or "1")
    note = ask("  Note (optional) > ").strip()
    return {
        "valid": True,
        "category": category,
        "subcategory": subcategory,
        "primary_range": {"index": primary, **spans[primary - 1]},
        "note": note,
    }


def label_clean(ask: Ask, say: Say) -> dict[str, Any]:
    raw = prompt(
        ask,
        say,
        "Clean change? [c] looks clean (Enter) / [s] suspicious > ",
        lambda a: a in ("", "c", "s"),
    )
    if raw == "s":
        return {
            "clean_verdict": "suspicious",
            "note": prompt(ask, say, "  What looks suspicious? > ", bool),
        }
    return {"clean_verdict": "looks clean", "note": ""}


def load_labels(path: Path) -> dict[str, dict[str, Any]]:
    """Latest record per case ID."""
    labels: dict[str, dict[str, Any]] = {}
    if path.exists():
        for line in path.read_text().splitlines():
            if line.strip():
                record = json.loads(line)
                labels[record["case_id"]] = record
    return labels


def run(
    cases: list[dict[str, Any]],
    labels_path: Path,
    ask: Ask,
    say: Say,
    color: bool = True,
    now: Callable[[], str] | None = None,
) -> int:
    """Label cases in order, starting at the first unlabelled one. Returns cases labelled."""
    now = now or (lambda: datetime.now(UTC).isoformat(timespec="seconds"))
    done = load_labels(labels_path)
    index = next((i for i, c in enumerate(cases) if c["case_id"] not in done), len(cases))
    labelled = 0
    say(f"{len(done)} of {len(cases)} cases already labelled. Keys: b = back one case, q = quit.")
    while index < len(cases):
        case = cases[index]
        say(render(case, index + 1, len(cases), color))
        try:
            fields = (
                label_buggy(case, ask, say) if case["kind"] == "buggy" else label_clean(ask, say)
            )
        except Back:
            index = max(0, index - 1)
            continue
        except Quit:
            say(f"Stopped. {labelled} labelled this session; progress saved to {labels_path}.")
            return labelled
        record = {
            "case_id": case["case_id"],
            "kind": case["kind"],
            "split": case["split"],
            "heuristic_category": case.get("category_label"),
            **fields,
            "labelled_at": now(),
        }
        labels_path.parent.mkdir(parents=True, exist_ok=True)
        with labels_path.open("a") as out:
            out.write(json.dumps(record) + "\n")
        labelled += 1
        index += 1
    say(f"All {len(cases)} cases labelled. Labels: {labels_path}")
    return labelled


def main(argv: list[str] | None = None, ask: Ask = input, say: Say = print) -> int:
    parser = argparse.ArgumentParser(description="Hand-label benchmark cases (Q61).")
    parser.add_argument("--split", choices=("dev", "holdout"), required=True)
    parser.add_argument(
        "--freeze",
        action="store_true",
        help="required for --split holdout: confirms prompt tuning is frozen",
    )
    parser.add_argument("--labels", type=Path, default=LABELS)
    parser.add_argument("--no-color", action="store_true")
    args = parser.parse_args(argv)
    if args.split == "holdout":
        say(
            "WARNING: the holdout split is labelled only after prompt tuning is frozen. "
            "Looking at holdout cases earlier leaks them into tuning decisions."
        )
        if not args.freeze:
            say("Refusing: pass --freeze to confirm prompt tuning is frozen.")
            return 2
    cases = [json.loads(line) for line in (DATA / f"{args.split}.jsonl").read_text().splitlines()]
    cases.sort(key=lambda c: c["case_id"])
    color = not args.no_color and sys.stdout.isatty()
    try:
        run(cases, args.labels, ask, say, color)
    except (KeyboardInterrupt, EOFError):
        say("\nStopped; progress so far is saved.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
