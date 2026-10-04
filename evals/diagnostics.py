"""Diagnostics behind the metrics (ADR-025): no LLM calls, cached results only.

- base_rate: share of each buggy case's changed lines inside its bug-holding ranges (±3). High
  values mean location matching cannot separate a reviewer from chance on this benchmark.
- miss_breakdown: why the reviewer missed strict location on a buggy case.
- coordinates: whether findings use new-file line numbers, as labels do, or cite removed lines
  by old-file number.
- clean_false_positives: category, severity, repo and size of every finding on a clean case.
- leak_split: detection and strict category-correct recall on cases whose removed lines carry
  issue references or telltale words, against the rest.
"""

import re
import statistics
from collections import Counter
from typing import Any

from evals.benchmark.leak_scan import scan
from evals.metrics import (
    MARGIN,
    SUSPICIOUS_CLEAN,
    case_hit,
    hits,
    rate,
    size_bucket,
    tier_spans,
)

HUNK = re.compile(r"^@@ -(\d+)(?:,\d+)? \+(\d+)(?:,\d+)? @@")


def diff_sides(diff: str) -> dict[str, dict[str, set[int]]]:
    """Per file: new-side shown lines, added lines, the new-side position of every change
    (additions and deletion points), and old-side removed lines."""
    out: dict[str, dict[str, set[int]]] = {}
    path: str | None = None
    old = new = 0
    for raw in diff.splitlines():
        if raw.startswith("+++ "):
            path = raw[6:] if raw.startswith("+++ b/") else None
            if path:
                out.setdefault(
                    path, {"shown": set(), "added": set(), "changed": set(), "removed_old": set()}
                )
            continue
        if raw.startswith(("diff --git", "--- ", "index ")):
            continue
        if match := HUNK.match(raw):
            old, new = int(match.group(1)), int(match.group(2))
            continue
        if path is None:
            continue
        sides = out[path]
        if raw.startswith("+"):
            sides["shown"].add(new)
            sides["added"].add(new)
            sides["changed"].add(new)
            new += 1
        elif raw.startswith("-"):
            sides["removed_old"].add(old)
            sides["changed"].add(new)  # the deletion point, in new-side coordinates
            old += 1
        elif raw.startswith(" "):
            sides["shown"].add(new)
            old += 1
            new += 1
    return out


def kept(cases: list[dict[str, Any]], labels: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    return [c for c in cases if c["kind"] == "buggy" and labels.get(c["case_id"], {}).get("valid")]


def base_rate(cases: list[dict[str, Any]], labels: dict[str, dict[str, Any]]) -> dict[str, Any]:
    shares = []
    for c in kept(cases, labels):
        spans = tier_spans(c, labels[c["case_id"]])["strict"]
        changed = [(f, n) for f, s in diff_sides(c["diff"]).items() for n in s["changed"]]
        if not changed:
            continue
        inside = sum(
            any(
                s["file"] == f and s["line_start"] - MARGIN <= n <= s["line_end"] + MARGIN
                for s in spans
            )
            for f, n in changed
        )
        shares.append(inside / len(changed))
    return {
        "cases": len(shares),
        "mean": statistics.fmean(shares) if shares else None,
        "median": statistics.median(shares) if shares else None,
        "all_changed_lines_inside": sum(x == 1.0 for x in shares),
        "distribution": {
            "100%": sum(x == 1.0 for x in shares),
            "75-99%": sum(0.75 <= x < 1.0 for x in shares),
            "50-74%": sum(0.5 <= x < 0.75 for x in shares),
            "<50%": sum(x < 0.5 for x in shares),
        },
    }


def finding_position(finding: dict[str, Any], sides: dict[str, dict[str, set[int]]]) -> str:
    file_sides = sides.get(finding["file"])
    if file_sides is None:
        return "file not in diff"
    lines = set(range(finding["line_start"], finding["line_end"] + 1))
    if lines & file_sides["added"]:
        return "new-side, on an added line"
    on_shown = bool(lines & file_sides["shown"])
    on_removed_old = bool(lines & file_sides["removed_old"])
    if on_shown and on_removed_old:
        return "ambiguous: new-side context or old-side removed line"
    if on_shown:
        return "new-side, context line"
    if on_removed_old:
        return "old-side only: cites a removed line by its old-file number"
    return "outside the diff on both sides"


def coordinates(cases: list[dict[str, Any]], findings: dict[str, list[Any]]) -> dict[str, Any]:
    counts: Counter[str] = Counter()
    old_side: list[str] = []
    for c in cases:
        sides = diff_sides(c["diff"])
        for f in findings.get(c["case_id"], []):
            position = finding_position(f, sides)
            counts[position] += 1
            if position.startswith(("old-side", "outside")):
                old_side.append(c["case_id"])
    return {
        "findings": sum(counts.values()),
        "positions": dict(counts.most_common()),
        "cases_off_new_side": sorted(set(old_side)),
    }


def miss_breakdown(
    cases: list[dict[str, Any]],
    labels: dict[str, dict[str, Any]],
    records: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    causes: dict[str, list[str]] = {}
    for c in kept(cases, labels):
        record = records[c["case_id"]]
        spans = tier_spans(c, labels[c["case_id"]])["strict"]
        found = record["findings"]
        if any(hits(f, s) for f in found for s in spans):
            continue
        if record["status"].startswith("failed"):
            cause = f"no usable answer ({record['status']})"
        elif not found:
            cause = "no findings"
        else:
            sides = diff_sides(c["diff"])
            positions = {finding_position(f, sides) for f in found}
            if any(p.startswith("new-side, on an added") for p in positions):
                cause = "findings on changed lines, outside the ±3 window"
            elif any(p.startswith("old-side") for p in positions):
                cause = "findings cite removed lines by old-file number"
            elif any(p.startswith(("new-side", "ambiguous")) for p in positions):
                cause = "findings on context lines, outside the ±3 window"
            else:
                cause = "findings outside the diff"
        causes.setdefault(cause, []).append(c["case_id"])
    return {
        "misses": sum(len(v) for v in causes.values()),
        "causes": {k: {"count": len(v), "cases": v} for k, v in sorted(causes.items())},
    }


def clean_false_positives(
    cases: list[dict[str, Any]], records: dict[str, dict[str, Any]]
) -> dict[str, Any]:
    flagged = [c for c in cases if c["kind"] == "clean" and records[c["case_id"]]["findings"]]
    findings = [(c, f) for c in flagged for f in records[c["case_id"]]["findings"]]
    clean = [c for c in cases if c["kind"] == "clean"]
    return {
        "flagged_cases": len(flagged),
        "findings": len(findings),
        "by_category": dict(Counter(f["category"] for _, f in findings).most_common()),
        "by_severity": dict(Counter(f["severity"] for _, f in findings).most_common()),
        "flagged_by_repo": {
            r: f"{sum(c['repo'] == r for c in flagged)}/{sum(c['repo'] == r for c in clean)}"
            for r in sorted({c["repo"] for c in clean})
        },
        "flagged_by_size": {
            b: f"{sum(size_bucket(c['size_lines']) == b for c in flagged)}/"
            f"{sum(size_bucket(c['size_lines']) == b for c in clean)}"
            for b in sorted({size_bucket(c["size_lines"]) for c in clean})
        },
        "suspicious_flagged": [
            cid for cid in SUSPICIOUS_CLEAN if cid in {c["case_id"] for c in flagged}
        ],
        "cases": [
            {
                "case_id": c["case_id"],
                "repo": c["repo"],
                "size": c["size_lines"],
                "suspicious": c["case_id"] in SUSPICIOUS_CLEAN,
                "findings": [
                    {
                        "category": f["category"],
                        "severity": f["severity"],
                        "message": f["message"][:160],
                    }
                    for f in records[c["case_id"]]["findings"]
                ],
            }
            for c in flagged
        ],
    }


def leak_cases(cases: list[dict[str, Any]]) -> set[str]:
    """Buggy cases whose removed lines match any leak-scan pattern."""
    return {cid for hits_ in scan(cases).values() for cid, _ in hits_.get("buggy", [])}


def leak_split(
    cases: list[dict[str, Any]],
    labels: dict[str, dict[str, Any]],
    records: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    flagged = leak_cases(cases)
    groups: dict[str, list[dict[str, Any]]] = {"leak-scan matches": [], "others": []}
    for c in kept(cases, labels):
        groups["leak-scan matches" if c["case_id"] in flagged else "others"].append(c)

    def summary(members: list[dict[str, Any]]) -> dict[str, Any]:
        detected = sum(bool(records[c["case_id"]]["findings"]) for c in members)
        correct = sum(
            case_hit(
                records[c["case_id"]]["findings"],
                tier_spans(c, labels[c["case_id"]])["strict"],
                labels[c["case_id"]]["category"],
            )[1]
            for c in members
        )
        return {
            "detection": rate(detected, len(members)),
            "strict_category_recall": rate(correct, len(members)),
        }

    return {
        name: {"cases": sorted(c["case_id"] for c in members), **summary(members)}
        for name, members in groups.items()
    }


def diagnostics(
    cases: list[dict[str, Any]],
    labels: dict[str, dict[str, Any]],
    records: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    return {
        "base_rate": base_rate(cases, labels),
        "strict_location_misses": miss_breakdown(cases, labels, records),
        "coordinates": coordinates(cases, {k: r["findings"] for k, r in records.items()}),
        "clean_false_positives": clean_false_positives(cases, records),
        "leak_split": leak_split(cases, labels, records),
    }


def attribution(
    cases: list[dict[str, Any]],
    before: dict[str, dict[str, Any]],
    after: dict[str, dict[str, Any]],
    step: dict[str, Any],
) -> dict[str, Any]:
    """Why outcomes changed between two runs (no LLM calls). For each case whose outcome
    changed on any McNemar field: did it need a validation retry in the later run, and was
    its earlier result affected by line numbering (findings citing old-file lines or outside
    the diff)? Cases in "neither" are most likely run-to-run variance."""
    by_id = {c["case_id"]: c for c in cases}
    changed = sorted({cid for m in step.values() for cid in m["first_only"] + m["second_only"]})
    groups: dict[str, list[str]] = {"retry": [], "numbering": [], "both": [], "neither": []}
    for cid in changed:
        retry = after[cid].get("validation_retries", 0) > 0
        sides = diff_sides(by_id[cid]["diff"])
        numbering = any(
            finding_position(f, sides).startswith(("old-side", "outside"))
            for f in before[cid]["findings"]
        )
        key = (
            "both"
            if retry and numbering
            else "retry"
            if retry
            else "numbering"
            if numbering
            else "neither"
        )
        groups[key].append(cid)
    return {"changed": len(changed), "groups": groups}
