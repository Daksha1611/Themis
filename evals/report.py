"""Baseline report: a completed eval run as a vault note (ADR-025 detection-first headline).

    python -m evals.report evals/results/<run_id> [--compare evals/results/<earlier_run>]

Writes docs/vault/08 Results/baseline-<split>-<date>.md from the run's summary.json. Every rate is
shown with its raw counts and a 95% Wilson interval, with the chance baseline beside it. With
--compare, the report adds a paired McNemar comparison against the earlier run on the same cases.
The Caveats section is required.
"""

import argparse
import json
from pathlib import Path
from typing import Any

from evals.benchmark.label import LABELS, load_labels
from evals.metrics import compare_runs, summarize

VAULT_RESULTS = Path("docs/vault/08 Results")
DATA = Path("evals/benchmark/data")
LABEL_REPORT = "label-report-dev-2026-10-03"


def fmt(r: dict[str, Any]) -> str:
    if not r["n"]:
        return "n/a (0/0)"
    return f"{r['rate']:.1%} ({r['k']}/{r['n']}; 95% CI {r['low']:.1%}–{r['high']:.1%})"


def fmt_j(j: dict[str, Any]) -> str:
    if j["j"] is None:
        return "n/a"
    return f"{j['j']:.3f} (95% CI {j['low']:.3f} to {j['high']:.3f})"


def mean(value: float | None, digits: int = 2) -> str:
    return "n/a" if value is None else f"{value:.{digits}f}"


def noise_floor(s: dict[str, Any]) -> str:
    nf = s["reviewer"]["false_positives"]["noise_floor"]
    return (
        f"noise floor: {nf['k']} of {nf['n']} dev clean cases ({nf['rate']:.1%}) are marked "
        "suspicious, so up to that share of the clean flag rate may be label noise"
    )


def base_rate_note(s: dict[str, Any]) -> str:
    br = s["diagnostics"]["base_rate"]
    return (
        f"on average {br['mean']:.1%} of a buggy case's changed lines lie inside its "
        f"bug-holding ranges ±3 (median {br['median']:.0%}; {br['all_changed_lines_inside']} "
        f"of {br['cases']} cases at 100%)"
    )


def headline(s: dict[str, Any]) -> list[str]:
    rev, ch = s["headline"]["reviewer"], s["headline"]["chance"]
    majority = s["chance_baseline"]["category"]
    return [
        "## Headline (ADR-025)",
        "",
        "| Metric | Reviewer | Chance baseline |",
        "|---|---|---|",
        f"| **Youden's J** = detection rate − clean flag rate | **{fmt_j(rev['youden_j'])}** | "
        f"{fmt_j(ch['youden_j'])} |",
        f"| **Strict category-correct recall** | **{fmt(rev['strict_category_recall'])}** | "
        f"{fmt(ch['strict_category_recall'])} |",
        f"| **Precision** (findings on a bug-holding range) | "
        f"**{fmt(rev['strict_location_precision'])}** | {fmt(ch['strict_location_precision'])} |",
        f"| **Clean flag rate** (FPR) | **{fmt(rev['clean_fpr'])}** | {fmt(ch['clean_fpr'])} |",
        f"| Detection rate (TPR) | {fmt(rev['detection_tpr'])} | {fmt(ch['detection_tpr'])} |",
        "",
        "- The chance baseline flags the first changed line of every hunk of every case as "
        f"`{majority}`. It detects every case and flags every clean case, so its J is 0. Its "
        "category-correct recall equals the majority-class rate: the share of kept buggy cases "
        f"labelled `{majority}`.",
        f"- Clean flag rate {noise_floor(s)}.",
    ]


def render(s: dict[str, Any], comparison: dict[str, Any] | None = None) -> str:
    rev, chance, op, sched = s["reviewer"], s["chance_baseline"], s["operational"], s["schedule"]
    dx = s["diagnostics"]
    fresh = list(s.get("fresh_cases", []))
    out = [
        f"# Baseline: {s['split']} split, {s['provider']}/{s['model']}",
        "",
        f"- Run: `{s['run_id']}` (git `{s['git_sha'][:7]}`"
        + (", **working tree dirty**" if s["git_dirty"] else "")
        + f"), finished {s['finished_at']}",
        f"- Pinned model ([[ADR-024 Eval runs pin a single provider and model]]): "
        f"`{s['provider']}/{s['model']}`, temperature {s['temperature']}, "
        f"max_tokens {s['max_tokens']}",
        f"- Scored cases: {rev['cases']['labelled_buggy']} kept buggy + {rev['cases']['clean']} "
        f"clean; case order shuffled with seed {s['order_seed']}",
        f"- Diff transform: `{s.get('diff_transform') or 'none'}` (issue references in removed "
        "lines masked; [[Benchmark]])",
    ]
    if fresh:
        out.append(
            f"- **This baseline includes a masked rerun:** {len(fresh)} cases whose diffs the "
            f"transform changed were called fresh ({', '.join(f'`{c}`' for c in fresh)}); the "
            f"other {op['cases'] - len(fresh)} came from the response cache, unchanged."
        )
    out += [
        f"- Raw evidence: `evals/results/{s['run_id']}/` (`results.jsonl`, `summary.json`)",
        "",
        *headline(s),
        "",
        "## Location matching: a diagnostic, not a headline",
        "",
        "**Location recall at ±3 lines is non-discriminating on this benchmark:** "
        + base_rate_note(s)
        + ". A reviewer that points anywhere in the diff lands on a labelled range, so the "
        "chance baseline scores higher than the reviewer.",
        "",
        "| Strict location recall | Reviewer | Chance baseline |",
        "|---|---|---|",
    ]
    for tol, r in rev["location_tolerance"].items():
        out.append(f"| {tol} lines | {fmt(r)} | {fmt(chance['location_tolerance'][tol])} |")
    out += [
        "",
        "| Tier | Mode | Reviewer | Chance baseline |",
        "|---|---|---|---|",
    ]
    names = {
        "lenient": "Lenient (any auto-labelled range)",
        "strict": "Strict (bug-holding ranges)",
        "primary": "Primary-only",
    }
    for tier in ("lenient", "strict", "primary"):
        for mode, label in (("location", "location-only ⚠"), ("category", "category-correct")):
            out.append(
                f"| {names[tier]} | {label} | {fmt(rev['recall'][tier][mode])} | "
                f"{fmt(chance['recall'][tier][mode])} |"
            )
    out += [
        "",
        "⚠ location-only rows are non-discriminating at ±3 (base rate above).",
        "",
        "## Micro and macro recall (strict, category-correct)",
        "",
        f"- Micro: {fmt(rev['recall']['strict']['category'])}",
        f"- Macro over categories with ≥{rev['macro']['floor']} kept cases: "
        f"{mean(rev['macro']['strict_category'], 3)} (a mean of per-category rates; counts below)",
        "",
        "| Category | Cases | Strict category-correct | Chance | Macro |",
        "|---|---|---|---|---|",
    ]
    for cat, v in sorted(rev["per_category"].items(), key=lambda x: (-x[1]["n"], x[0])):
        eligible = "yes" if cat in rev["macro"]["categories"] else "no (below floor)"
        out.append(
            f"| {cat} | {v['n']} | {fmt(v['strict_category'])} | "
            f"{fmt(chance['per_category'][cat]['strict_category'])} | {eligible} |"
        )
    fp = rev["false_positives"]
    out += [
        "",
        "## Clean cases",
        "",
        f"Every rate here carries the clean-case {noise_floor(s)}.",
        "",
        f"- Clean flag rate: {fmt(fp['overall']['cases_with_finding'])}; mean findings per "
        f"clean case {mean(fp['overall']['mean_findings'])}. Chance baseline: "
        f"{fmt(chance['false_positives']['overall']['cases_with_finding'])}.",
        "",
        "| Group | Clean cases with ≥1 finding | Mean findings |",
        "|---|---|---|",
    ]
    for kind, title in (("by_size", "size"), ("by_repo", "repo")):
        for group, v in fp[kind].items():
            out.append(
                f"| {title} {group} | {fmt(v['cases_with_finding'])} | {mean(v['mean_findings'])} |"
            )
    cfp = dx["clean_false_positives"]
    out += [
        "",
        f"**False-positive pattern** ({cfp['findings']} findings on {cfp['flagged_cases']} clean "
        f"cases): by category {cfp['by_category']}; by severity {cfp['by_severity']}; flagged "
        f"by size {cfp['flagged_by_size']}; by repo {cfp['flagged_by_repo']}. Suspicious clean "
        f"cases flagged: {', '.join(f'`{c}`' for c in cfp['suspicious_flagged']) or 'none'} "
        "(possibly true positives; see the label report).",
        "",
        "## Recall by repo and by size (strict, category-correct)",
        "",
        "| Group | Recall |",
        "|---|---|",
        *(f"| repo {g} | {fmt(r)} |" for g, r in rev["recall_by_repo"].items()),
        *(f"| size {g} lines | {fmt(r)} |" for g, r in rev["recall_by_size"].items()),
        "",
        "## Diagnostics",
        "",
    ]
    misses = dx["strict_location_misses"]
    out.append(f"**Strict-location misses: {misses['misses']}.**")
    out.append("")
    for cause, v in misses["causes"].items():
        out.append(f"- {cause}: {v['count']} ({', '.join(f'`{c}`' for c in v['cases'])})")
    co = dx["coordinates"]
    out += [
        "",
        f"**Line coordinates** ({co['findings']} findings): {co['positions']}. Most findings "
        "use new-file lines, as the labels do. A few cite removed lines by their old-file "
        "numbers, a convention the prompt does not set (Q65).",
        "",
    ]
    ls = dx["leak_split"]
    out.append("**Leak split** (cases whose removed lines matched the leak scan vs the rest):")
    out.append("")
    for group, v in ls.items():
        out.append(
            f"- {group} ({len(v['cases'])}): detection {fmt(v['detection'])}; strict "
            f"category-correct {fmt(v['strict_category_recall'])}"
        )
    if comparison:
        out += ["", f"**Paired comparison with `{comparison['against']}`** (exact McNemar):", ""]
        for field, m in comparison["mcnemar"].items():
            out.append(
                f"- {field}: b = {m['b']} (earlier only), c = {m['c']} (this run only), "
                f"{m['n_pairs']} pairs, p = {m['p_value']:.3f}"
            )
    out += [
        "",
        "## Security",
        "",
        "Raw counts only; **not statistically meaningful** (too few cases, Q58): "
        + ", ".join(
            f"{cat} {v['k']}/{v['n']}" for cat, v in rev["security"]["per_category"].items()
        )
        + ".",
        "",
        "## Operations",
        "",
        f"- Cases answered: {op['answered']}/{op['cases']}; status: {op['status']}",
        f"- Failures by type: {op['failures'] or 'none'}",
        f"- Parse-error rate: {fmt(op['parse_error_rate'])}",
        f"- Cost: mean {mean(op['cost_usd_estimate']['mean_per_case'], 5)} USD per case, total "
        f"{op['cost_usd_estimate']['total']:.4f} USD ({op['cost_usd_estimate']['note']})",
        f"- Latency: mean {mean(op['latency_ms']['mean'], 0)} ms, p95 "
        f"{mean(op['latency_ms']['p95'], 0)} ms (original call latency, also for cached cases)",
        f"- Tokens: prompt {op['tokens']['prompt']}, completion {op['tokens']['completion']}",
        f"- Cache: {fmt(op['cache']['hit_rate'])} cases served from cache; provider attempts "
        f"{op['cache']['provider_attempts']}",
        f"- Provider/model of answered cases: {op['provider_models']}; pinned-model share "
        f"{fmt(op['pinned_share'])}; identical model ID across sessions: "
        f"{sched['model_identical_across_sessions']}",
        "",
        "## Caveats",
        "",
    ]
    if not sched["model_identical_across_sessions"]:
        out.append(
            "- ⚠ **The provider returned different model identifiers across sessions** "
            f"({sched['models_by_session']}): the run may mix model versions."
        )
    if op["pinned_share"]["rate"] != 1.0:
        out.append(
            "- ⚠ **Not every answered case came from the pinned model** "
            f"({fmt(op['pinned_share'])})."
        )
    if op["failures"]:
        out.append(f"- ⚠ Failed cases count as misses: {op['failures']}.")
    out += [
        "- **Location matching is non-discriminating on this benchmark:** "
        + base_rate_note(s)
        + ". Location recall at ±3 is reported as a diagnostic only ([[ADR-025 Detection-first "
        "metrics]]).",
        "- **Labels:** LLM-assigned from human-written upstream evidence. The owner verified "
        "them on a 28-case sample (25 stratified + 3 borderline): 25/25 agreement per field "
        f"(95% lower bound 86.7%) ([[{LABEL_REPORT}]], [[Benchmark]]).",
        f"- **Clean-case {noise_floor(s)}.** Two of the three suspicious cases were flagged; one "
        "(click `3fe0fe03`) demonstrably introduced later bugs, and SZZ missed it because the "
        "code moved ([[Benchmark Leakage]]).",
        "- **Category concentration:** `type-or-contract` is 34 of 80 kept cases (43%), which "
        "is also the chance baseline's category-correct recall. Macro recall covers only four "
        "categories, with the counts shown beside it.",
        "- **Security is not measurable** here: 2 kept security cases.",
        "- **Leakage profile:** 92% of buggy cases are after mid-2025; `Textualize/rich` has the "
        "weakest date profile ([[Benchmark Leakage]]). Issue references in removed lines are "
        "masked (`mask-issue-refs-v1`).",
        "- **Single run:** run-to-run variance is not measured yet (Q63). The masked cases are "
        "fresh samples, so part of any change on them is that variance.",
        "- **Diff-only review:** every eval case gets a neutral PR title to prevent label "
        "leakage; production passes the real title, so production performance may differ "
        "([[Eval Harness]]).",
        "- **Line-coordinate convention (Q65):** findings about removed code sometimes cite "
        "old-file line numbers; labels use new-file lines.",
    ]
    return "\n".join(out) + "\n"


FRONTMATTER = """---
name: {name}
description: "{description}"
type: reliability
status: done
tags: [reliability, results]
related:
  - "[[Metrics]]"
  - "[[Benchmark]]"
  - "[[Eval Harness]]"
  - "[[ADR-025 Detection-first metrics]]"
  - "[[{label_report}]]"
---

"""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("run_dir", type=Path)
    parser.add_argument("--compare", type=Path, help="an earlier run on the same cases")
    args = parser.parse_args(argv)
    summary = json.loads((args.run_dir / "summary.json").read_text())
    if "diagnostics" not in summary:  # summaries written before ADR-025: recompute from cache
        cases = [
            json.loads(x) for x in (DATA / f"{summary['split']}.jsonl").read_text().splitlines()
        ]
        summary = summarize(args.run_dir, cases, load_labels(LABELS))
    records = [
        json.loads(line)
        for line in (args.run_dir / "results.jsonl").read_text().splitlines()
        if line.strip()
    ]
    summary["fresh_cases"] = sorted(
        r["case_id"] for r in records if r.get("diff_masked") and not r["cached"]
    )
    comparison = None
    if args.compare:
        cases = [
            json.loads(x) for x in (DATA / f"{summary['split']}.jsonl").read_text().splitlines()
        ]
        comparison = {
            "against": args.compare.name,
            "mcnemar": compare_runs(args.compare, args.run_dir, cases, load_labels(LABELS)),
        }
    name = f"baseline-{summary['split']}-{summary['finished_at'][:10]}"
    path = VAULT_RESULTS / f"{name}.md"
    description = (
        f"Baseline eval of the {summary['split']} split on the pinned model: Youden's J, "
        "category-correct recall, precision, clean flag rate, chance baseline, diagnostics, "
        "caveats."
    )
    front = FRONTMATTER.format(name=name, description=description, label_report=LABEL_REPORT)
    path.write_text(front + render(summary, comparison))
    print(f"wrote {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
