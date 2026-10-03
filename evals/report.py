"""Baseline report (M3 Step 7): a completed eval run as a vault note.

    python -m evals.report evals/results/<run_id>

Writes docs/vault/08 Results/baseline-<split>-<date>.md from the run's summary.json and run.json.
Every rate is shown with its raw counts and 95% Wilson interval. The Caveats section is required.
"""

import argparse
import json
from pathlib import Path
from typing import Any

VAULT_RESULTS = Path("docs/vault/08 Results")
LABEL_REPORT = "label-report-dev-2026-10-03"


def fmt(r: dict[str, Any]) -> str:
    if not r["n"]:
        return "n/a (0/0)"
    return f"{r['rate']:.1%} ({r['k']}/{r['n']}; 95% CI {r['low']:.1%}–{r['high']:.1%})"


def mean(value: float | None, digits: int = 2) -> str:
    return "n/a" if value is None else f"{value:.{digits}f}"


def noise_floor(s: dict[str, Any]) -> str:
    nf = s["reviewer"]["false_positives"]["noise_floor"]
    return (
        f"noise floor: {nf['k']} of {nf['n']} dev clean cases ({nf['rate']:.1%}) are marked "
        "suspicious, so up to that share of the false-positive rate may be label noise"
    )


def render(s: dict[str, Any], leak: dict[str, Any] | None = None) -> str:
    rev, chance, op, sched = s["reviewer"], s["chance_baseline"], s["operational"], s["schedule"]
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
        f"- Location match: {s['match']['rule']}, ±{s['match']['margin_lines']} lines "
        "([[Metrics]])",
        f"- Raw evidence: `evals/results/{s['run_id']}/` (`results.jsonl`, `summary.json`)",
        "",
        "## Headline",
        "",
        f"- **Strict, category-correct recall:** {fmt(s['headline']['strict_category_recall'])}",
        f"- **Precision (strict, location):** {fmt(s['headline']['strict_location_precision'])}",
        f"- **False-positive rate on clean cases:** {fmt(s['headline']['clean_fp_rate'])}; "
        + noise_floor(s),
        "",
        "## Recall: three tiers, two matching modes, against the chance baseline",
        "",
        "The chance baseline flags the first changed line of every hunk as "
        f"`{chance['category']}` (no LLM).",
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
        for mode, label in (("location", "location-only"), ("category", "category-correct")):
            out.append(
                f"| {names[tier]} | {label} | {fmt(rev['recall'][tier][mode])} | "
                f"{fmt(chance['recall'][tier][mode])} |"
            )
    out += [
        "",
        "Exact-line (strict ranges, no margin): location "
        f"{fmt(rev['exact_line']['location'])}; category-correct "
        f"{fmt(rev['exact_line']['category'])}.",
        "",
        "## Micro and macro recall (strict)",
        "",
        f"- Micro, category-correct: {fmt(rev['recall']['strict']['category'])}",
        f"- Macro over categories with ≥{rev['macro']['floor']} kept cases: category-correct "
        f"{mean(rev['macro']['strict_category'], 3)}, location "
        f"{mean(rev['macro']['strict_location'], 3)}"
        " (a mean of per-category rates; counts below)",
        "",
        "| Category | Cases | Strict location | Strict category-correct | Macro |",
        "|---|---|---|---|---|",
    ]
    for cat, v in sorted(rev["per_category"].items(), key=lambda x: (-x[1]["n"], x[0])):
        eligible = "yes" if cat in rev["macro"]["categories"] else "no (below floor)"
        out.append(
            f"| {cat} | {v['n']} | {fmt(v['strict_location'])} | {fmt(v['strict_category'])} | "
            f"{eligible} |"
        )
    out += [
        "",
        "## Precision",
        "",
        f"{rev['findings']['total']} findings in all, {rev['findings']['on_clean']} on clean "
        f"cases (chance baseline: {chance['findings']['total']}, "
        f"{chance['findings']['on_clean']}).",
        "",
        "| Precision | Reviewer | Chance baseline |",
        "|---|---|---|",
    ]
    for key in ("strict_location", "strict_category", "lenient_location", "lenient_category"):
        out.append(
            f"| {key.replace('_', ', ')} | {fmt(rev['precision'][key])} | "
            f"{fmt(chance['precision'][key])} |"
        )
    fp = rev["false_positives"]
    out += [
        "",
        "## False positives on clean cases",
        "",
        f"Every rate here carries the clean-case {noise_floor(s)}.",
        "",
        f"- Overall: {fmt(fp['overall']['cases_with_finding'])} of clean cases have ≥1 finding; "
        f"mean findings per clean case {mean(fp['overall']['mean_findings'])}. Chance baseline: "
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
    out += [
        "",
        "## Strict category-correct recall by repo and by size",
        "",
        "| Group | Recall |",
        "|---|---|",
        *(f"| repo {g} | {fmt(r)} |" for g, r in rev["recall_by_repo"].items()),
        *(f"| size {g} lines | {fmt(r)} |" for g, r in rev["recall_by_size"].items()),
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
        f"- Tokens: prompt {op['tokens']['prompt']}, completion {op['tokens']['completion']}; "
        f"estimated prompt tokens {op['tokens']['estimated_prompt']} vs actual "
        f"{op['tokens']['actual_prompt_answered']} on answered cases",
        f"- Cache: {fmt(op['cache']['hit_rate'])} cases served from cache; provider attempts "
        f"{op['cache']['provider_attempts']}",
        f"- Provider/model of answered cases: {op['provider_models']}; pinned-model share "
        f"{fmt(op['pinned_share'])}",
        "",
        "## Schedule",
        "",
        "| Session | Started | Ended | Stop | Cases |",
        "|---|---|---|---|---|",
    ]
    for sess in sched["sessions"]:
        n = len(sched["cases_by_session"].get(str(sess["session"]), []))
        out.append(
            f"| {sess['session']} | {sess['started_at']} | {sess.get('ended_at', '')} | "
            f"{sess.get('stop', '')} | {n} |"
        )
    out += [
        "",
        "Cases per UTC day: "
        + ", ".join(f"{d} {len(ids)}" for d, ids in sched["cases_by_utc_day"].items())
        + f". Model identifiers per session: {sched['models_by_session']}.",
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
        "- **Labels:** LLM-assigned from human-written upstream evidence. The owner verified "
        "them on a 28-case sample (25 stratified + 3 borderline): 25/25 agreement per field "
        f"(95% lower bound 86.7%) ([[{LABEL_REPORT}]], [[Benchmark]]).",
        f"- **Clean-case {noise_floor(s)}.** One suspicious case (click `3fe0fe03`) demonstrably "
        "introduced later bugs; SZZ missed it because the code moved ([[Benchmark Leakage]]).",
        "- **Category concentration:** `type-or-contract` is 34 of 80 kept cases (43%); macro "
        "recall covers only four categories, with the counts shown beside it.",
        "- **Security is not measurable** here: 2 kept security cases.",
        "- **Leakage profile:** 92% of buggy cases are after mid-2025; `Textualize/rich` has the "
        "weakest date profile ([[Benchmark Leakage]]).",
        "- **Single run:** run-to-run variance is not measured yet (Q63).",
        "- **Diff-only review:** every eval case gets a neutral PR title to prevent label leakage; "
        "production passes the real title, so production performance may differ "
        "([[Eval Harness]]).",
    ]
    if leak:
        out.append(
            f"- **Leak scan:** {leak['buggy']} of {leak['buggy_total']} buggy diffs (and "
            f"{leak['clean']} of {leak['clean_total']} clean) have issue references or telltale "
            "words in their removed lines, mostly comments citing the fixed issue; not changed "
            "pending the owner's decision ([[Benchmark]])."
        )
    return "\n".join(out) + "\n"


FRONTMATTER = """---
name: {name}
description: "Baseline eval of the {split} split on the pinned model: recall tiers, \
precision, false positives, chance baseline, caveats."
type: reliability
status: done
tags: [reliability, results]
related:
  - "[[Metrics]]"
  - "[[Benchmark]]"
  - "[[Eval Harness]]"
  - "[[{label_report}]]"
---

"""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("run_dir", type=Path)
    parser.add_argument("--leak", help="leak-scan counts as buggy/buggy_total/clean/clean_total")
    args = parser.parse_args(argv)
    summary = json.loads((args.run_dir / "summary.json").read_text())
    leak = None
    if args.leak:
        b, bt, c, ct = (int(x) for x in args.leak.split("/"))
        leak = {"buggy": b, "buggy_total": bt, "clean": c, "clean_total": ct}
    name = f"baseline-{summary['split']}-{summary['finished_at'][:10]}"
    path = VAULT_RESULTS / f"{name}.md"
    front = FRONTMATTER.format(name=name, split=summary["split"], label_report=LABEL_REPORT)
    path.write_text(front + render(summary, leak))
    print(f"wrote {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
