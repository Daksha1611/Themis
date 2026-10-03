"""Eval metrics (M3 Step 6). Definitions: docs/vault/03 Reliability/Metrics.md.

Location match (Q23): a finding hits a labelled range when it names the same file and its line
range overlaps the labelled range widened by MARGIN lines on each side (exact-line: no margin).
Recall has three tiers (Q62): lenient = any auto-labelled range; strict = any range recorded as
holding the bug (primary + primary_contested_with); primary-only. Each tier is reported
location-only and category-correct (a location hit whose category matches the label). Failed
cases count as misses and are reported by failure type. Every rate carries k/n and a 95% Wilson
score interval.
"""

import json
import math
import statistics
from collections import Counter, defaultdict
from collections.abc import Iterable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from evals.benchmark.label_report import MACRO_MIN

MARGIN = 3
TIERS = ("lenient", "strict", "primary")
MODES = ("location", "category")
SIZE_BUCKETS = ((1, 5), (6, 15), (16, 30), (31, 60))
SECURITY_PREFIXES = ("CWE-", "security-other")
NOISE_SUSPICIOUS, NOISE_CLEAN = 3, 41  # dev clean cases marked suspicious (label report)
SCHEMA_VERSION = 1

Span = dict[str, Any]
Finding = dict[str, Any]


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """95% Wilson score interval for k/n; (0, 1) when n is 0."""
    if n == 0:
        return 0.0, 1.0
    p = k / n
    centre = p + z * z / (2 * n)
    spread = z * math.sqrt((p * (1 - p) + z * z / (4 * n)) / n)
    denominator = 1 + z * z / n
    return max(0.0, (centre - spread) / denominator), min(1.0, (centre + spread) / denominator)


def rate(k: int, n: int) -> dict[str, Any]:
    low, high = wilson(k, n)
    return {"k": k, "n": n, "rate": k / n if n else None, "low": low, "high": high}


def hits(finding: Finding, span: Span, margin: int = MARGIN) -> bool:
    return bool(
        finding["file"] == span["file"]
        and finding["line_start"] <= span["line_end"] + margin
        and finding["line_end"] >= span["line_start"] - margin
    )


def tier_spans(case: dict[str, Any], label: dict[str, Any] | None) -> dict[str, list[Span]]:
    """Ranges per tier. Without a label (unlabelled holdout) only the lenient tier exists."""
    spans: dict[str, list[Span]] = {"lenient": case["labels"], "strict": [], "primary": []}
    if label and label.get("valid"):
        primary = label["primary_range"]["index"]
        holding = sorted({primary, *label.get("primary_contested_with", [])})
        spans["strict"] = [case["labels"][i - 1] for i in holding]
        spans["primary"] = [case["labels"][primary - 1]]
    return spans


def case_hit(
    findings: list[Finding], spans: list[Span], category: str | None, margin: int = MARGIN
) -> tuple[bool, bool]:
    """(location hit, category-correct hit) for one case."""
    located = [f for f in findings if any(hits(f, s, margin) for s in spans)]
    return bool(located), any(category is not None and f["category"] == category for f in located)


def size_bucket(lines: int) -> str:
    for low, high in SIZE_BUCKETS:
        if low <= lines <= high:
            return f"{low}-{high}"
    return f">{SIZE_BUCKETS[-1][1]}"


def first_changed_lines(diff: str) -> list[tuple[str, int]]:
    """(file, new-side line) of the first changed line of every hunk. A hunk with no added line
    contributes its new-side start (where the removal happened)."""
    out: list[tuple[str, int]] = []
    path: str | None = None
    new_line = 0
    pending: tuple[str, int] | None = None
    for raw in diff.splitlines():
        if raw.startswith("+++ "):
            path = raw[6:] if raw.startswith("+++ b/") else None
            continue
        if raw.startswith(("diff --git", "--- ", "index ")):
            continue
        if raw.startswith("@@"):
            if pending:
                out.append(pending)
            new_line = int(raw.split("+", 1)[1].split(",")[0].split(" ")[0])
            pending = (path, new_line) if path else None
            continue
        if raw.startswith("+"):
            if pending and path:
                out.append((path, new_line))
                pending = None
            new_line += 1
        elif raw.startswith(" "):
            new_line += 1
    if pending:
        out.append(pending)
    return out


def chance_findings(case: dict[str, Any], category: str) -> list[Finding]:
    """The chance baseline: the first changed line of every hunk, filed under `category`."""
    return [
        {"file": file, "line_start": line, "line_end": line, "category": category}
        for file, line in first_changed_lines(case["diff"])
    ]


def most_common_category(labels: dict[str, dict[str, Any]]) -> str:
    counts = Counter(r["category"] for r in labels.values() if r.get("valid"))
    return str(counts.most_common(1)[0][0])


def evaluate(
    cases: list[dict[str, Any]],
    labels: dict[str, dict[str, Any]],
    findings: dict[str, list[Finding]],
) -> dict[str, Any]:
    """Quality metrics for one reviewer (findings per case ID) over the scored cases."""
    buggy = [c for c in cases if c["kind"] == "buggy"]
    clean = [c for c in cases if c["kind"] == "clean"]
    labelled = [c for c in buggy if labels.get(c["case_id"], {}).get("valid")]

    outcome: dict[str, dict[str, dict[str, bool]]] = {}
    for c in buggy:
        label = labels.get(c["case_id"])
        category = label["category"] if label and label.get("valid") else None
        spans = tier_spans(c, label)
        outcome[c["case_id"]] = {}
        for tier in TIERS:
            loc, cat = case_hit(findings.get(c["case_id"], []), spans[tier], category)
            outcome[c["case_id"]][tier] = {"location": loc, "category": cat}
        loc, cat = case_hit(findings.get(c["case_id"], []), spans["strict"], category, margin=0)
        outcome[c["case_id"]]["exact"] = {"location": loc, "category": cat}

    def recall(subset: list[dict[str, Any]], tier: str, mode: str) -> dict[str, Any]:
        return rate(sum(outcome[c["case_id"]][tier][mode] for c in subset), len(subset))

    recall_tiers = {
        tier: {
            "location": recall(buggy if tier == "lenient" else labelled, tier, "location"),
            "category": recall(labelled, tier, "category"),
        }
        for tier in TIERS
    }
    by_category: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for c in labelled:
        by_category[labels[c["case_id"]]["category"]].append(c)
    per_category: dict[str, dict[str, Any]] = {
        cat: {
            "n": len(members),
            "strict_location": recall(members, "strict", "location"),
            "strict_category": recall(members, "strict", "category"),
        }
        for cat, members in sorted(by_category.items())
    }
    eligible = [cat for cat, v in per_category.items() if v["n"] >= MACRO_MIN]
    macro = {
        mode: statistics.fmean(per_category[c][f"strict_{mode}"]["rate"] for c in eligible)
        if eligible
        else None
        for mode in MODES
    }

    all_findings = [(c, f) for c in cases for f in findings.get(c["case_id"], [])]

    def precision(tier: str, mode: str) -> dict[str, Any]:
        good = 0
        for c, f in all_findings:
            if c["kind"] != "buggy":
                continue
            label = labels.get(c["case_id"])
            spans = tier_spans(c, label)[tier]
            if any(hits(f, s) for s in spans) and (
                mode == "location" or (label is not None and f["category"] == label["category"])
            ):
                good += 1
        return rate(good, len(all_findings))

    def false_positives(subset: list[dict[str, Any]]) -> dict[str, Any]:
        counts = [len(findings.get(c["case_id"], [])) for c in subset]
        return {
            "cases_with_finding": rate(sum(n > 0 for n in counts), len(subset)),
            "mean_findings": statistics.fmean(counts) if counts else None,
        }

    def grouped(key: Any) -> dict[str, Any]:
        groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for c in clean:
            groups[key(c)].append(c)
        return {g: false_positives(members) for g, members in sorted(groups.items())}

    def recall_by(key: Any) -> dict[str, Any]:
        groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for c in labelled:
            groups[key(c)].append(c)
        return {g: recall(m, "strict", "category") for g, m in sorted(groups.items())}

    security = {
        cat: v["strict_category"]
        for cat, v in per_category.items()
        if cat.startswith(SECURITY_PREFIXES)
    }
    return {
        "cases": {"buggy": len(buggy), "labelled_buggy": len(labelled), "clean": len(clean)},
        "recall": recall_tiers,
        "exact_line": {mode: recall(labelled, "exact", mode) for mode in MODES},
        "macro": {
            "floor": MACRO_MIN,
            "categories": {c: per_category[c]["n"] for c in eligible},
            "strict_location": macro["location"],
            "strict_category": macro["category"],
        },
        "per_category": per_category,
        "recall_by_repo": recall_by(lambda c: c["repo"]),
        "recall_by_size": recall_by(lambda c: size_bucket(c["size_lines"])),
        "precision": {
            f"{tier}_{mode}": precision(tier, mode)
            for tier in ("strict", "lenient")
            for mode in MODES
        },
        "findings": {
            "total": len(all_findings),
            "on_clean": sum(c["kind"] == "clean" for c, _ in all_findings),
        },
        "false_positives": {
            "overall": false_positives(clean),
            "by_size": grouped(lambda c: size_bucket(c["size_lines"])),
            "by_repo": grouped(lambda c: c["repo"]),
            "noise_floor": {
                "note": "dev clean cases marked suspicious; up to this share of the FP rate "
                "may be label noise",
                **rate(NOISE_SUSPICIOUS, NOISE_CLEAN),
            },
        },
        "security": {"per_category": security, "note": "not statistically meaningful"},
    }


def p95(values: list[float]) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    return ordered[min(len(ordered) - 1, math.ceil(0.95 * len(ordered)) - 1)]


def operational(records: Iterable[dict[str, Any]]) -> dict[str, Any]:
    """Cost, latency, failures, parse errors, tokens, cache use, provider/model provenance."""
    records = list(records)
    answered = [r for r in records if r["model"] is not None]
    latencies = [r["latency_ms"] for r in answered if r["latency_ms"] is not None]
    pinned = [
        r
        for r in answered
        if (r["provider"], r["model"]) == (r["pinned_provider"], r["pinned_model"])
    ]
    status = Counter(r["status"] for r in records)
    return {
        "cases": len(records),
        "answered": len(answered),
        "status": dict(sorted(status.items())),
        "failures": {k: v for k, v in sorted(status.items()) if k.startswith("failed")},
        "parse_error_rate": rate(sum(bool(r["parse_errors"]) for r in answered), len(answered)),
        "cost_usd_estimate": {
            "note": "LiteLLM list-price estimate; actual free-tier spend is $0",
            "mean_per_case": statistics.fmean(r["cost_usd_estimate"] for r in answered)
            if answered
            else None,
            "total": sum(r["cost_usd_estimate"] for r in answered),
        },
        "latency_ms": {
            "mean": statistics.fmean(latencies) if latencies else None,
            "p95": p95([float(x) for x in latencies]),
        },
        "tokens": {
            "prompt": sum(r["prompt_tokens"] for r in records),
            "completion": sum(r["completion_tokens"] for r in records),
            "estimated_prompt": sum(r["estimated_prompt_tokens"] for r in answered),
            "actual_prompt_answered": sum(r["prompt_tokens"] for r in answered),
        },
        "cache": {
            "cached_cases": sum(r["cached"] for r in records),
            "hit_rate": rate(sum(r["cached"] for r in records), len(records)),
            "provider_attempts": sum(r["provider_attempts"] for r in records),
        },
        "provider_models": dict(Counter(f"{r['provider']}/{r['model']}" for r in answered)),
        "pinned_share": rate(len(pinned), len(answered)),
    }


def load_results(run_dir: Path) -> list[dict[str, Any]]:
    path = run_dir / "results.jsonl"
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def summarize(
    run_dir: Path, cases: list[dict[str, Any]], labels: dict[str, dict[str, Any]]
) -> dict[str, Any]:
    meta = json.loads((run_dir / "run.json").read_text())
    records = {r["case_id"]: r for r in load_results(run_dir)}
    scored = [c for c in cases if c["case_id"] in records]
    reviewer = evaluate(scored, labels, {cid: r["findings"] for cid, r in records.items()})
    top = most_common_category(labels)
    chance = evaluate(scored, labels, {c["case_id"]: chance_findings(c, top) for c in scored})
    headline = {
        "strict_category_recall": reviewer["recall"]["strict"]["category"],
        "strict_location_precision": reviewer["precision"]["strict_location"],
        "clean_fp_rate": reviewer["false_positives"]["overall"]["cases_with_finding"],
        "noise_floor": reviewer["false_positives"]["noise_floor"],
    }
    return {
        "schema_version": SCHEMA_VERSION,
        **{k: meta[k] for k in ("run_id", "split", "git_sha", "git_dirty", "provider", "model")},
        **{k: meta[k] for k in ("temperature", "max_tokens", "started_at", "cache_mode")},
        "finished_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "match": {"margin_lines": MARGIN, "rule": "same file, line ranges overlap"},
        "headline": headline,
        "reviewer": reviewer,
        "chance_baseline": {"category": top, **chance},
        "operational": operational(records.values()),
    }


def write_summary(
    run_dir: Path, cases: list[dict[str, Any]], labels: dict[str, dict[str, Any]]
) -> dict[str, Any]:
    summary = summarize(run_dir, cases, labels)
    (run_dir / "summary.json").write_text(json.dumps(summary, indent=1) + "\n")
    return summary
