"""Agreement across independent review runs, from the cache (M5 pivot, ADR-031). No LLM calls.

    python -m evals.agreement

Findings of different runs of the same case are matched: same file, line ranges within ±3 of
each other, and (strict) the same category, or (location) any category. Matching findings form
clusters (connected components over the match relation); a cluster's support is the number of
distinct runs in it, and every finding's agreement count is its cluster's support.

Voting rule "flag if >= m of k runs agree": a case's merged review keeps one finding per cluster
with support >= m (the member with the median start line; in location mode the category most
members give). The merged review is scored like any reviewer (J, detection, clean flag rate,
precision, strict category-correct recall), with stratified bootstrap 95% CIs over cases, beside
the single-run reference (the mean of the k runs) and the chance baseline.

Two analyses: (a) v1, v1 rerun and v2 (k = 3); (b) v1 and v1 rerun only (k = 2): identical
configuration, so their disagreement is pure sampling noise. Writes
`docs/vault/08 Results/agreement-dev-<date>.md` and `evals/results/agreement-dev/agreement.json`.
"""

import json
import statistics
from collections import Counter
from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from evals.benchmark.label import LABELS, load_labels
from evals.metrics import (
    MARGIN,
    bootstrap_ci,
    case_hit,
    chance_findings,
    hits,
    most_common_category,
    permutation_test,
    tier_spans,
)
from evals.runner import scored_cases

RUNS = {
    "v1": Path("evals/results/dev-20261004T085157Z-ad2fc7d"),
    "v1-rerun": Path("evals/results/dev-20261004T130632Z-1033b35"),
    "v2": Path("evals/results/dev-20261004T140940Z-4feea8e"),
}
ANALYSES = {"a": ("v1", "v1-rerun", "v2"), "b": ("v1", "v1-rerun")}
OUT = Path("evals/results/agreement-dev")
VAULT = Path("docs/vault/08 Results")
BOOTSTRAP = 2000
SEED = 20261029
MAX_DETECTION_DROP = 0.05

Finding = dict[str, Any]
Cases = list[dict[str, Any]]
Labels = dict[str, dict[str, Any]]


def load_run(run_dir: Path) -> dict[str, list[Finding]]:
    records = [json.loads(x) for x in (run_dir / "results.jsonl").read_text().splitlines() if x]
    return {r["case_id"]: r["findings"] for r in records}


def matches(f: Finding, g: Finding, strict: bool, margin: int = MARGIN) -> bool:
    return bool(
        f["file"] == g["file"]
        and f["line_start"] <= g["line_end"] + margin
        and f["line_end"] >= g["line_start"] - margin
        and (not strict or f["category"] == g["category"])
    )


def clusters(per_run: Sequence[list[Finding]], strict: bool) -> list[list[tuple[int, Finding]]]:
    """Connected components of matching findings across runs (findings of the same run are
    joined only through a finding of another run)."""
    items = [(r, f) for r, findings in enumerate(per_run) for f in findings]
    parent = list(range(len(items)))

    def find(i: int) -> int:
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    for i, (ri, fi) in enumerate(items):
        for j in range(i + 1, len(items)):
            rj, fj = items[j]
            if ri != rj and matches(fi, fj, strict):
                parent[find(i)] = find(j)
    groups: dict[int, list[tuple[int, Finding]]] = {}
    for i, item in enumerate(items):
        groups.setdefault(find(i), []).append(item)
    return list(groups.values())


def support(cluster: list[tuple[int, Finding]]) -> int:
    return len({r for r, _ in cluster})


def representative(cluster: list[tuple[int, Finding]], strict: bool) -> Finding:
    members = sorted((f for _, f in cluster), key=lambda f: (f["line_start"], f["line_end"]))
    chosen = dict(members[(len(members) - 1) // 2])
    if not strict:
        votes = Counter(f["category"] for _, f in cluster)
        top = max(votes.values())
        first = next(f["category"] for _, f in sorted(cluster, key=lambda x: x[0]))
        chosen["category"] = (
            first if votes[first] == top else next(c for c, n in votes.items() if n == top)
        )
    return chosen


def voted(
    cases: Cases, runs: Sequence[dict[str, list[Finding]]], m: int, strict: bool
) -> dict[str, list[Finding]]:
    """Per case, the merged review under "flag if >= m runs agree"."""
    return {
        c["case_id"]: [
            representative(cl, strict)
            for cl in clusters([run.get(c["case_id"], []) for run in runs], strict)
            if support(cl) >= m
        ]
        for c in cases
    }


def is_real(f: Finding, case: dict[str, Any], label: dict[str, Any] | None) -> bool:
    return case["kind"] == "buggy" and any(hits(f, s) for s in tier_spans(case, label)["strict"])


def case_stats(
    cases: Cases, labels: Labels, findings: dict[str, list[Finding]]
) -> list[dict[str, Any]]:
    """Per scored case: flagged (>= 1 finding), strict category-correct, findings, real ones."""
    out = []
    for c in cases:
        found = findings.get(c["case_id"], [])
        label = labels.get(c["case_id"])
        category = label["category"] if label and label.get("valid") else None
        _, cat = case_hit(found, tier_spans(c, label)["strict"], category)
        out.append(
            {
                "kind": c["kind"],
                "flagged": float(bool(found)),
                "category": float(cat),
                "findings": float(len(found)),
                "real": float(sum(is_real(f, c, label) for f in found)),
            }
        )
    return out


def mean_stats(per_run: list[list[dict[str, Any]]]) -> list[dict[str, Any]]:
    """Per case, the mean over runs of every statistic: the single-run reference."""
    return [
        {
            "kind": rows[0]["kind"],
            **{k: statistics.fmean(r[k] for r in rows) for k in rows[0] if k != "kind"},
        }
        for rows in zip(*per_run, strict=True)
    ]


def headline(stats: list[dict[str, Any]]) -> dict[str, float]:
    buggy = [s for s in stats if s["kind"] == "buggy"]
    clean = [s for s in stats if s["kind"] == "clean"]
    detection = statistics.fmean(s["flagged"] for s in buggy)
    clean_flag = statistics.fmean(s["flagged"] for s in clean)
    total = sum(s["findings"] for s in stats)
    return {
        "j": detection - clean_flag,
        "detection": detection,
        "clean_flag": clean_flag,
        "precision": sum(s["real"] for s in stats) / total if total else 0.0,
        "category": statistics.fmean(s["category"] for s in buggy),
        "findings": total,
    }


def bootstrap(stats: list[dict[str, Any]], reps: int = BOOTSTRAP) -> dict[str, list[float]]:
    """Stratified percentile bootstrap (buggy and clean resampled separately) for each
    headline measure."""
    import numpy as np  # noqa: PLC0415 (eval statistics only)

    rng = np.random.default_rng(SEED)
    buggy = [s for s in stats if s["kind"] == "buggy"]
    clean = [s for s in stats if s["kind"] == "clean"]
    draws: dict[str, list[float]] = {k: [] for k in headline(stats) if k != "findings"}
    for _ in range(reps):
        sample = [buggy[i] for i in rng.integers(0, len(buggy), len(buggy))] + [
            clean[i] for i in rng.integers(0, len(clean), len(clean))
        ]
        h = headline(sample)
        for k in draws:
            draws[k].append(h[k])
    return {
        k: [float(np.quantile(v, 0.025)), float(np.quantile(v, 0.975))] for k, v in draws.items()
    }


def distribution(
    cases: Cases, labels: Labels, runs: Sequence[dict[str, list[Finding]]], strict: bool
) -> dict[str, dict[int, int]]:
    """Agreement count of every finding of every run, split real vs noise."""
    out: dict[str, dict[int, int]] = {"real": Counter(), "noise": Counter()}
    for c in cases:
        label = labels.get(c["case_id"])
        for cl in clusters([run.get(c["case_id"], []) for run in runs], strict):
            n = support(cl)
            for _, f in cl:
                out["real" if is_real(f, c, label) else "noise"][n] += 1
    return {k: dict(sorted(v.items())) for k, v in out.items()}


def analyse(cases: Cases, labels: Labels, names: Sequence[str]) -> dict[str, Any]:
    runs = [load_run(RUNS[n]) for n in names]
    single = mean_stats([case_stats(cases, labels, run) for run in runs])
    rows: dict[str, Any] = {"single run (mean of k)": single}
    for strict in (True, False):
        mode = "strict" if strict else "location"
        for m in range(1, len(runs) + 1):
            rows[f"{mode}, >= {m} of {len(runs)}"] = case_stats(
                cases, labels, voted(cases, runs, m, strict)
            )
    chance_category = most_common_category(labels)
    rows["chance baseline"] = case_stats(
        cases, labels, {c["case_id"]: chance_findings(c, chance_category) for c in cases}
    )
    return {
        "runs": list(names),
        "paired": paired(rows),
        "distribution": {
            mode: distribution(cases, labels, runs, mode == "strict")
            for mode in ("strict", "location")
        },
        "rules": {
            name: {"point": headline(stats), "ci95": bootstrap(stats)}
            for name, stats in rows.items()
        },
    }


def paired(rows: dict[str, list[dict[str, Any]]]) -> dict[str, dict[str, Any]]:
    """Each voting rule vs the single-run reference, paired by case (ADR-029): net cases for
    detection (buggy), clean flags and category-correct, with the bootstrap CI and the
    permutation p-value."""
    ref = rows["single run (mean of k)"]
    out: dict[str, dict[str, Any]] = {}
    for name, stats in rows.items():
        if name in ("single run (mean of k)", "chance baseline"):
            continue
        out[name] = {}
        for measure, kind, key in (
            ("detection", "buggy", "flagged"),
            ("clean_flags", "clean", "flagged"),
            ("category", "buggy", "category"),
        ):
            diffs = [b[key] - a[key] for a, b in zip(ref, stats, strict=True) if a["kind"] == kind]
            low, high = bootstrap_ci(diffs)
            out[name][measure] = {
                "net_cases": sum(diffs),
                "ci95": [low, high],
                "p_value": permutation_test(diffs),
            }
    return out


def separation(result: dict[str, Any]) -> list[tuple[str, float, float]]:
    """Rules that keep detection within MAX_DETECTION_DROP of the single-run reference, with
    their clean flag rate change (negative = fewer clean cases flagged)."""
    rules = result["rules"]
    ref = rules["single run (mean of k)"]["point"]
    out = []
    for name, v in rules.items():
        if name in ("single run (mean of k)", "chance baseline"):
            continue
        drop = ref["detection"] - v["point"]["detection"]
        if drop <= MAX_DETECTION_DROP + 1e-9:
            out.append((name, drop, v["point"]["clean_flag"] - ref["clean_flag"]))
    return out


def pct(x: float) -> str:
    return f"{100 * x:.1f}%"


def render(results: dict[str, dict[str, Any]]) -> str:
    today = datetime.now(UTC).date().isoformat()
    lines = [
        "---",
        f"name: agreement-dev-{today}",
        'description: "Agreement of findings across cached dev runs (v1, v1 rerun, v2) and '
        'the voting rule flag-if-m-of-k-agree, with bootstrap CIs (ADR-031 Step 1)."',
        "type: reliability",
        "status: done",
        "tags: [reliability, results]",
        "related:",
        '  - "[[ADR-031 Consistency-based precision filter]]"',
        '  - "[[Precision Filter]]"',
        '  - "[[precision-filter-dev-2026-10-29]]"',
        '  - "[[ADR-029 Aggregated evaluation]]"',
        "---",
        "",
        f"# Agreement across runs, dev split ({today})",
        "",
        "From the cached runs; **no LLM calls**, holdout untouched. Matching: same file, line "
        f"ranges within ±{MARGIN}, and the same category (**strict**) or any category "
        "(**location**). Clusters are connected components of matching findings; a finding's "
        "agreement count is the number of runs in its cluster. Real or noise as in "
        "[[precision-filter-dev-2026-10-29]] (within ±3 of a strict bug-holding range of a "
        "buggy case). Voting keeps one finding per cluster with at least m runs. CIs: stratified "
        f"percentile bootstrap over cases ({BOOTSTRAP} resamples). The single-run reference is "
        "the mean of the k runs.",
        "",
    ]
    titles = {
        "a": "(a) v1, v1 rerun and v2 (k = 3)",
        "b": "(b) v1 and v1 rerun only (k = 2, identical configuration)",
    }
    for key, result in results.items():
        k = len(result["runs"])
        lines += [
            f"## {titles[key]}",
            "",
            "**Agreement count of each finding** (findings, all runs):",
            "",
        ]
        lines += [
            "| Mode | Kind | "
            + " | ".join(f"{n} of {k}" for n in range(1, k + 1))
            + " | Share at ≥ 2 |"
        ]
        lines += ["|---|---|" + "---|" * k + "---|"]
        for mode, dist in result["distribution"].items():
            for kind in ("real", "noise"):
                counts = [dist[kind].get(n, 0) for n in range(1, k + 1)]
                total = sum(counts)
                agreed = sum(counts[1:]) / total if total else 0.0
                lines.append(
                    f"| {mode} | {kind} | " + " | ".join(map(str, counts)) + f" | {pct(agreed)} |"
                )
        lines += [
            "",
            "**Voting rules:**",
            "",
            "| Rule | J | Detection | Clean flag rate | Precision | Category-correct | Findings |",
            "|---|---|---|---|---|---|---|",
        ]
        for name, v in result["rules"].items():
            p, ci = v["point"], v["ci95"]

            def cell(key: str, as_pct: bool = True, p: dict[str, float] = p, ci: Any = ci) -> str:
                f = pct if as_pct else (lambda x: f"{x:.3f}")
                return f"{f(p[key])} ({f(ci[key][0])} to {f(ci[key][1])})"

            lines.append(
                f"| {name} | {cell('j', False)} | {cell('detection')} | {cell('clean_flag')} | "
                f"{cell('precision')} | {cell('category')} | {p['findings']:.0f} |"
            )
        lines += [
            "",
            "**Paired against the single-run reference** (net cases, bootstrap 95% CI, "
            "permutation p; negative = fewer):",
            "",
            "| Rule | Detection (of 80) | Clean flags (of 41) | Category-correct (of 80) |",
            "|---|---|---|---|",
        ]
        for name, v in result["paired"].items():

            def net(x: dict[str, Any]) -> str:
                lo, hi = x["ci95"]
                return f"{x['net_cases']:+.2f} ({lo:+.1f} to {hi:+.1f}), p = {x['p_value']:.3f}"

            lines.append(
                f"| {name} | {net(v['detection'])} | {net(v['clean_flags'])} | "
                f"{net(v['category'])} |"
            )
        ok = separation(result)
        lines += ["", "**Rules within 5 points of single-run detection:** "]
        lines[-1] += (
            "; ".join(
                f"{n} (detection {-100 * d:+.1f} points, clean flag rate {100 * c:+.1f} points)"
                for n, d, c in ok
            )
            if ok
            else "none."
        )
        lines.append("")
    return "\n".join(lines)


def gate(result: dict[str, Any]) -> list[str]:
    """ADR-031's build gate: rules whose detection stays within MAX_DETECTION_DROP of the
    single-run reference and whose clean-flag reduction is material (paired 95% CI below 0)."""
    passing = {name for name, _, _ in separation(result)}
    return [
        name
        for name, v in result["paired"].items()
        if name in passing and v["clean_flags"]["ci95"][1] < 0
    ]


def gate_section(results: dict[str, dict[str, Any]]) -> list[str]:
    lines = ["## Gate for building the filter (ADR-031 Step 2)", ""]
    lines.append(
        "Build only if a rule cuts the clean flag rate materially (paired 95% CI on clean-flag "
        "net cases entirely below 0) while detection stays within "
        f"{int(MAX_DETECTION_DROP * 100)} points of the single-run reference."
    )
    lines.append("")
    for key, result in results.items():
        passed = gate(result)
        lines.append(
            f"- **({key}):** " + (", ".join(passed) + " pass." if passed else "no rule passes.")
        )
    lines.append("")
    return lines


def main() -> int:
    labels = load_labels(LABELS)
    cases = scored_cases("dev", labels)
    results = {key: analyse(cases, labels, names) for key, names in ANALYSES.items()}
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "agreement.json").write_text(json.dumps(results, indent=1) + "\n")
    page = render(results) + "\n".join(gate_section(results))
    path = VAULT / f"agreement-dev-{datetime.now(UTC).date().isoformat()}.md"
    path.write_text(page)
    print(page)
    print(f"written: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
