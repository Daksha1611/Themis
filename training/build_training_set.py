"""Build the precision filter's training set from cached dev runs (M5, ADR-030). No LLM calls.

    python -m training.build_training_set

Every finding of the cached dev runs (baseline v1, its identical rerun, v2) becomes one row,
auto-labelled by location:
- real (1): on a buggy case, within ±3 lines of a strict bug-holding range (the same test as
  the headline precision, so the filter is trained on what precision counts);
- noise (0): any finding on a clean case, or a finding off every strict range of a buggy case.
The labels are location-based: a correct finding about an issue nobody labelled counts as noise.

Dev only (ADR-017): any case ID present in the holdout split is rejected, whatever the run.
"""

import json
from pathlib import Path
from typing import Any

from evals.benchmark.label import DATA, LABELS, load_labels
from evals.metrics import hits, tier_spans
from evals.runner import mask_issue_refs, scored_cases

RUNS = {
    "v1": Path("evals/results/dev-20261004T085157Z-ad2fc7d"),
    "v1-rerun": Path("evals/results/dev-20261004T130632Z-1033b35"),
    "v2": Path("evals/results/dev-20261004T140940Z-4feea8e"),
}
OUT = Path("training/data/training_set.jsonl")
LABEL_RULE = "location-v1: real = within ±3 of a strict bug-holding range of a buggy case"


class HoldoutLeak(ValueError):
    """A holdout case reached the precision filter's training data (ADR-017)."""


def holdout_ids(data: Path = DATA) -> set[str]:
    return {
        json.loads(line)["case_id"]
        for line in (data / "holdout.jsonl").read_text().splitlines()
        if line.strip()
    }


def require_dev_only(case_ids: set[str], holdout: set[str]) -> None:
    leaked = sorted(case_ids & holdout)
    if leaked:
        raise HoldoutLeak(f"{len(leaked)} holdout case(s) in the training data: {leaked[:5]}")


def diff_index(diff: str) -> dict[str, dict[int, tuple[str, int, int]]]:
    """Per file, new-file line -> (kind "+" or " ", hunk number, changed lines in the hunk)."""
    out: dict[str, dict[int, tuple[str, int, int]]] = {}
    path: str | None = None
    hunk, new = 0, 0
    pending: list[tuple[int, str]] = []

    def flush() -> None:
        if path is not None and pending:
            changed = sum(kind == "+" for _, kind in pending) + removed[0]
            for line, kind in pending:
                out.setdefault(path, {})[line] = (kind, hunk, changed)
        pending.clear()
        removed[0] = 0

    removed = [0]
    for raw in diff.splitlines():
        if raw.startswith("+++ "):
            flush()
            path = raw[6:] if raw.startswith("+++ b/") else None
        elif raw.startswith(("diff --git", "--- ", "index ")):
            continue
        elif raw.startswith("@@"):
            flush()
            hunk += 1
            new = int(raw.split("+", 1)[1].split(",", 1)[0].split(" ", 1)[0])
        elif raw.startswith("+"):
            pending.append((new, "+"))
            new += 1
        elif raw.startswith("-"):
            removed[0] += 1
        elif raw.startswith(" "):
            pending.append((new, " "))
            new += 1
    flush()
    return out


def snippet(diff: str, finding: dict[str, Any], around: int = 2) -> str:
    """The finding's lines from the diff (new side, with +/space markers), plus context."""
    lines: list[str] = []
    path: str | None = None
    new = 0
    low, high = finding["line_start"] - around, finding["line_end"] + around
    for raw in diff.splitlines():
        if raw.startswith("+++ "):
            path = raw[6:] if raw.startswith("+++ b/") else None
        elif raw.startswith(("diff --git", "--- ", "index ")):
            continue
        elif raw.startswith("@@"):
            new = int(raw.split("+", 1)[1].split(",", 1)[0].split(" ", 1)[0])
        elif raw.startswith(("+", " ")):
            if path == finding["file"] and low <= new <= high:
                lines.append(raw)
            new += 1
    return "\n".join(lines)


def features(
    finding: dict[str, Any], case: dict[str, Any], index: dict[str, Any]
) -> dict[str, Any]:
    """The reference model's inputs, all available when a review is posted."""
    span = range(finding["line_start"], finding["line_end"] + 1)
    seen = [index.get(finding["file"], {}).get(n) for n in span]
    known = [s for s in seen if s is not None]
    return {
        "category": finding["category"],
        "severity": finding["severity"],
        "raw_llm_confidence": float(finding.get("raw_llm_confidence") or 0.0),
        "message_chars": len(finding["message"]),
        "suggestion_chars": len(finding.get("suggestion") or ""),
        "span_lines": len(span),
        "on_changed_line": float(any(kind == "+" for kind, _, _ in known)),
        "hunk_changed_lines": max((size for _, _, size in known), default=0),
        "diff_changed_lines": int(case["size_lines"]),
    }


def is_real(finding: dict[str, Any], case: dict[str, Any], label: dict[str, Any] | None) -> int:
    if case["kind"] != "buggy":
        return 0
    return int(any(hits(finding, s) for s in tier_spans(case, label)["strict"]))


def build(runs: dict[str, Path] = RUNS) -> list[dict[str, Any]]:
    labels = load_labels(LABELS)
    cases = {c["case_id"]: c for c in scored_cases("dev", labels)}
    holdout = holdout_ids()
    rows: list[dict[str, Any]] = []
    for run, run_dir in runs.items():
        records = [json.loads(x) for x in (run_dir / "results.jsonl").read_text().splitlines() if x]
        require_dev_only({r["case_id"] for r in records}, holdout)
        for record in records:
            case = cases[record["case_id"]]
            diff = mask_issue_refs(case["diff"])
            index = diff_index(diff)
            for number, finding in enumerate(record["findings"]):
                rows.append(
                    {
                        "run": run,
                        "case_id": case["case_id"],
                        "kind": case["kind"],
                        "repo": case["repo"],
                        "finding_index": number,
                        "finding": finding,
                        "label": is_real(finding, case, labels.get(case["case_id"])),
                        "features": features(finding, case, index),
                        "snippet": snippet(diff, finding),
                    }
                )
    require_dev_only({r["case_id"] for r in rows}, holdout)
    return rows


def main() -> int:
    rows = build()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("".join(json.dumps(r) + "\n" for r in rows))
    real = sum(r["label"] for r in rows)
    cases = len({r["case_id"] for r in rows})
    print(f"{len(rows)} findings from {cases} dev cases: {real} real, {len(rows) - real} noise")
    print(f"label rule: {LABEL_RULE}; written to {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
