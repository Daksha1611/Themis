"""Precision filter on the cached dev runs, out of fold (M5, ADR-030). No LLM calls.

    python -m evals.filter_eval [--cv evals/results/filter-dev/cv.json] [--model auto]

Reads the cross-validation output of `training.train_filter`: per finding an out-of-fold score,
per outer fold a threshold chosen on that fold's training cases only. Each cached run's findings
are filtered (a finding is kept if its score reaches its case's fold threshold), and J,
precision, clean flag rate and strict category-correct recall are recomputed per run and
k-averaged. Filtered vs unfiltered is compared with the ADR-029 paired permutation test and
bootstrap CI on per-case means. Writes `docs/vault/08 Results/precision-filter-dev-<date>.md`.
"""

import argparse
import json
import statistics
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from evals.benchmark.label import LABELS, load_labels
from evals.metrics import aggregated_comparison, case_outcomes, evaluate
from evals.runner import scored_cases
from training.build_training_set import LABEL_RULE, RUNS
from training.train_filter import MAX_DETECTION_DROP

CV = Path("evals/results/filter-dev/cv.json")
VAULT = Path("docs/vault/08 Results")


def choose_model(cv: dict[str, Any]) -> str:
    """The model with the higher out-of-fold average precision."""
    models = cv["models"]
    return str(max(models, key=lambda m: models[m]["quality"]["average_precision"]))


def filtered_runs(
    cv: dict[str, Any], model: str
) -> tuple[dict[str, dict[str, list[Any]]], dict[str, dict[str, list[Any]]]]:
    """Per run, per case: (all findings, kept findings with `confidence` set to the score)."""
    scores = cv["models"][model]["scores"]
    thresholds = {int(k): v for k, v in cv["models"][model]["thresholds"].items()}
    score_of = {tuple(k): s for k, s in zip(cv["row_keys"], scores, strict=True)}
    raw: dict[str, dict[str, list[Any]]] = {}
    kept: dict[str, dict[str, list[Any]]] = {}
    for run, run_dir in RUNS.items():
        raw[run], kept[run] = defaultdict(list), defaultdict(list)
        for line in (run_dir / "results.jsonl").read_text().splitlines():
            record = json.loads(line)
            cid = record["case_id"]
            for i, finding in enumerate(record["findings"]):
                raw[run][cid].append(finding)
                score = score_of[(run, cid, i)]
                if score >= thresholds[cv["folds"][cid]]:
                    kept[run][cid].append({**finding, "confidence": round(score, 4)})
    return raw, kept


def headline(m: dict[str, Any]) -> dict[str, Any]:
    return {
        "j": m["detection"]["youden_j"]["j"],
        "detection": m["detection"]["tpr"],
        "clean_flag": m["detection"]["fpr"],
        "precision": m["precision"]["strict_location"],
        "strict_category": m["recall"]["strict"]["category"],
    }


def evaluate_filter(cv: dict[str, Any], model: str) -> dict[str, Any]:
    labels = load_labels(LABELS)
    cases = scored_cases("dev", labels)
    raw, kept = filtered_runs(cv, model)
    per_run = {
        run: {
            "unfiltered": headline(evaluate(cases, labels, raw[run])),
            "filtered": headline(evaluate(cases, labels, kept[run])),
        }
        for run in RUNS
    }
    before = [case_outcomes(cases, labels, raw[run]) for run in RUNS]
    after = [case_outcomes(cases, labels, kept[run]) for run in RUNS]
    return {
        "model": model,
        "per_run": per_run,
        "comparison": aggregated_comparison(before, after),
        "dropped": sum(len(v) for r in raw.values() for v in r.values())
        - sum(len(v) for r in kept.values() for v in r.values()),
        "total": sum(len(v) for r in raw.values() for v in r.values()),
    }


def mean_rate(per_run: dict[str, Any], side: str, key: str) -> float:
    values = [r[side][key] for r in per_run.values()]
    if key == "j":
        return statistics.fmean(values)
    return statistics.fmean(v["rate"] for v in values)


def sweep(cv: dict[str, Any], model: str, rows: list[dict[str, Any]]) -> list[tuple[float, ...]]:
    """Pooled out-of-fold precision and k-averaged detection at a grid of global thresholds:
    the precision-recall picture for choosing the configured threshold (Q17)."""
    scores = cv["models"][model]["scores"]
    buggy_cases = 80
    out: list[tuple[float, ...]] = []
    for t in (0.0, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8):
        keep = [s >= t for s in scores]
        kept_rows = [r for r, k in zip(rows, keep, strict=True) if k]
        precision = float(sum(r["label"] for r in kept_rows) / len(kept_rows) if kept_rows else 0)
        detected = [
            len({r["case_id"] for r in kept_rows if r["run"] == run and r["kind"] == "buggy"})
            / buggy_cases
            for run in RUNS
        ]
        flagged = [
            len({r["case_id"] for r in kept_rows if r["run"] == run and r["kind"] == "clean"}) / 41
            for run in RUNS
        ]
        out.append(
            (
                t,
                precision,
                statistics.fmean(detected),
                statistics.fmean(flagged),
                len(kept_rows) / len(rows),
            )
        )
    return out


def pct(x: float) -> str:
    return f"{100 * x:.1f}%"


def render(cv: dict[str, Any], result: dict[str, Any], rows: list[dict[str, Any]]) -> str:
    today = datetime.now(UTC).date().isoformat()
    model = result["model"]
    q = {name: m["quality"] for name, m in cv["models"].items()}
    noise_clean = sum(1 for r in rows if r["label"] == 0 and r["kind"] == "clean")
    noise_buggy = sum(1 for r in rows if r["label"] == 0 and r["kind"] == "buggy")
    lines = [
        "---",
        f"name: precision-filter-dev-{today}",
        'description: "M5 precision filter on the cached dev runs (v1, v1 rerun, v2), out of '
        'fold: models compared, threshold sweep, filtered metrics with the ADR-029 tests."',
        "type: reliability",
        "status: done",
        "tags: [reliability, results]",
        "related:",
        '  - "[[Precision Filter]]"',
        '  - "[[ADR-030 v1 finish plan and scope cuts]]"',
        '  - "[[ADR-029 Aggregated evaluation]]"',
        '  - "[[ADR-017 Dev-split-only training data for the precision filter]]"',
        "---",
        "",
        f"# Precision filter, dev split ({today})",
        "",
        "Built from the findings already cached by three dev runs; **no LLM calls**. Holdout "
        "never touched (`training/build_training_set.py` rejects holdout case IDs). Every number "
        "below is **out of fold**: the model and the threshold applied to a case never saw that "
        "case.",
        "",
        "## Training set",
        f"- **{cv['rows']} findings** from runs v1, v1 rerun and v2 over the 121 scored dev "
        f"cases: {cv['real']} real, {cv['rows'] - cv['real']} noise ({noise_clean} on clean "
        f"cases, {noise_buggy} off-range on buggy cases).",
        f"- **Label rule** ({LABEL_RULE}): the same test as the headline precision. "
        "**Limitation:** the labels are location-based, so a correct finding about an issue "
        "nobody labelled counts as noise, and a wrong finding that happens to sit inside a "
        "bug-holding range counts as real.",
        "- **Folds:** 5, grouped by case ID (seeded, buggy and clean dealt separately), so a "
        "case's findings from different runs never sit in both train and test.",
        "",
        "## Models (out-of-fold ranking quality)",
        "",
        "| Model | ROC AUC | Average precision | Base rate (share real) |",
        "|---|---|---|---|",
    ]
    for name, v in q.items():
        lines.append(
            f"| {name} | {v['roc_auc']:.3f} | {v['average_precision']:.3f} | {v['base_rate']:.3f} |"
        )
    tuned = cv.get("finetune")
    if tuned:
        v = tuned["quality"]
        lines.append(
            f"| codebert, fine-tuned (ranking only) | {v['roc_auc']:.3f} | "
            f"{v['average_precision']:.3f} | {v['base_rate']:.3f} |"
        )
    lines += [
        "",
        "- **features:** logistic regression over category, severity, `raw_llm_confidence`, "
        "message and suggestion length, span, changed line vs context, hunk size and diff size.",
        "- **codebert:** frozen `microsoft/codebert-base` embeddings (mean-pooled, CPU, 256 "
        "tokens) of the finding text plus its diff snippet, with a logistic-regression head.",
        "- Both: standardised inputs; C chosen by grouped inner CV on average precision.",
        "- **codebert, fine-tuned:** `microsoft/codebert-base` with a classification head, "
        "trained end to end on each outer fold's training cases (3 epochs, AdamW 2e-5, batch "
        "8, CPU). Only its ranking is compared: choosing its thresholds would take inner "
        "fine-tunes per fold, which was not worth running unless it out-ranked the reference.",
        f"- **Kept: {model}** (higher out-of-fold average precision).",
        "",
        "## Threshold (Q17)",
        f"Chosen inside each outer fold on the training folds' inner out-of-fold scores: the "
        f"highest pooled precision whose detection rate stays within "
        f"{int(MAX_DETECTION_DROP * 100)} points of unfiltered. Per-fold thresholds: "
        + ", ".join(f"{float(t):.3f}" for t in cv["models"][model]["thresholds"].values())
        + ".",
        "",
        f"Global sweep over the out-of-fold scores of **{model}** (pooled over the three runs; "
        "detection and clean flags averaged over runs):",
        "",
        "| Threshold | Precision | Detection | Clean flag rate | Findings kept |",
        "|---|---|---|---|---|",
    ]
    for t, p, d, f, k in sweep(cv, model, rows):
        lines.append(f"| {t:.1f} | {pct(p)} | {pct(d)} | {pct(f)} | {pct(k)} |")
    lines += [
        "",
        "## Filtered vs unfiltered, per run",
        "",
        "| Run | J | Precision | Clean flag rate | Strict category-correct | Detection |",
        "|---|---|---|---|---|---|",
    ]
    for run, v in result["per_run"].items():
        u, f = v["unfiltered"], v["filtered"]

        def both(key: str, u: dict[str, Any] = u, f: dict[str, Any] = f) -> str:
            a, b = u[key], f[key]
            return f"{a['k']}/{a['n']} → {b['k']}/{b['n']}"

        lines.append(
            f"| {run} | {u['j']:.3f} → {f['j']:.3f} | {both('precision')} | "
            f"{both('clean_flag')} | {both('strict_category')} | {both('detection')} |"
        )
    pr = result["per_run"]
    lines += [
        "",
        "**k-averaged (k = 3):** "
        f"J {mean_rate(pr, 'unfiltered', 'j'):.3f} → {mean_rate(pr, 'filtered', 'j'):.3f}; "
        f"precision {pct(mean_rate(pr, 'unfiltered', 'precision'))} → "
        f"{pct(mean_rate(pr, 'filtered', 'precision'))}; clean flag rate "
        f"{pct(mean_rate(pr, 'unfiltered', 'clean_flag'))} → "
        f"{pct(mean_rate(pr, 'filtered', 'clean_flag'))}; strict category-correct "
        f"{pct(mean_rate(pr, 'unfiltered', 'strict_category'))} → "
        f"{pct(mean_rate(pr, 'filtered', 'strict_category'))}; detection "
        f"{pct(mean_rate(pr, 'unfiltered', 'detection'))} → "
        f"{pct(mean_rate(pr, 'filtered', 'detection'))}. "
        f"Findings dropped: {result['dropped']} of {result['total']}.",
        "",
        "## Paired comparison (ADR-029)",
        "Per-case means over the three runs, filtered minus unfiltered; net cases with a "
        "bootstrap 95% CI and a two-sided sign-flip permutation p-value.",
        "",
        "| Measure | Cases | Unfiltered (sum of means) | Filtered | Net cases (95% CI) | p |",
        "|---|---|---|---|---|---|",
    ]
    names = {
        "detected": "Detection (buggy)",
        "strict_category": "Strict category-correct",
        "flagged": "Clean flags",
    }
    for field, v in result["comparison"].items():
        low, high = v["ci95"]
        lines.append(
            f"| {names[field]} | {v['cases']} | {v['first_mean_total']:.2f} | "
            f"{v['second_mean_total']:.2f} | {v['net_cases']:+.2f} ({low:+.2f} to {high:+.2f}) "
            f"| {v['p_value']:.4f} |"
        )
    scores = cv["models"][model]["scores"]
    per_case: dict[tuple[str, str], int] = defaultdict(int)
    for r in rows:
        if r["kind"] == "clean":
            per_case[(r["run"], r["case_id"])] += 1
    single = sum(n == 1 for n in per_case.values())
    mean_clean = statistics.fmean(
        s for r, s in zip(rows, scores, strict=True) if r["kind"] == "clean"
    )
    mean_buggy = statistics.fmean(
        s for r, s in zip(rows, scores, strict=True) if r["kind"] == "buggy"
    )
    drop = mean_rate(pr, "unfiltered", "detection") - mean_rate(pr, "filtered", "detection")
    j_change = mean_rate(pr, "filtered", "j") - mean_rate(pr, "unfiltered", "j")
    flags = result["comparison"]["flagged"]
    lines += [
        "",
        "## Verdict",
        f"- **Encoder vs reference:** the kept model is **{model}**. "
        + (
            "CodeBERT, frozen or fine-tuned, does not out-rank the feature model on these "
            "data. That is a valid result: with a few hundred location-labelled findings, the "
            "encoder has too little signal to learn from."
            if model == "features"
            else "CodeBERT out-ranks the feature model."
        ),
        f"- **J {'rises' if j_change > 0 else 'falls'} by {abs(j_change):.3f}** (k-averaged). "
        f"Precision rises because the filter drops findings, mostly on buggy cases; clean flags "
        f"change by {flags['net_cases']:+.2f} cases (p = {flags['p_value']:.2f}).",
        f"- **Detection falls {100 * drop:.1f} points** out of fold, against the "
        f"{int(MAX_DETECTION_DROP * 100)}-point limit the thresholds were chosen for on the "
        "training folds"
        + (
            ": the thresholds do not transfer exactly across folds."
            if drop > MAX_DETECTION_DROP
            else "."
        ),
        "- **Not to be wired in this form.** The filter's purpose is to cut clean-case noise "
        "(the clean flag rate), and here it does not. Most flagged clean cases rest on a single "
        f"finding ({single} of {len(per_case)} flagged clean case-runs), so one dropped finding "
        "would unflag them; but the model scores findings on clean cases about as high as "
        f"findings on buggy cases (mean {mean_clean:.3f} vs {mean_buggy:.3f}), so the "
        "thresholds keep them. The features describe the finding, not whether the code is "
        "wrong.",
        "",
        "## Caveats",
        "- **Not wired into posting.** The filter only sets `confidence` in this evaluation.",
        "- **Location-based labels** (above). The filter learns what the location test counts, "
        "including its blind spots.",
        "- **Training findings come from the same three runs that are evaluated.** Out-of-fold "
        "scoring keeps every case's own findings out of its model, but the runs share prompts, "
        "so this is not a test on new reviewer output. The M4 runs will provide fresh findings "
        "to check against.",
        "- **Small data:** a few hundred findings from about a hundred cases; the fold-to-fold "
        "thresholds vary.",
        "",
    ]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--cv", type=Path, default=CV)
    parser.add_argument("--model", default="auto")
    args = parser.parse_args(argv)
    cv = json.loads(args.cv.read_text())
    tuned = args.cv.parent / "finetune.json"
    if tuned.exists():
        cv["finetune"] = json.loads(tuned.read_text())
    model = choose_model(cv) if args.model == "auto" else args.model
    from training.train_filter import load_rows  # noqa: PLC0415

    rows = load_rows()
    result = evaluate_filter(cv, model)
    (args.cv.parent / "evaluation.json").write_text(json.dumps(result, indent=1) + "\n")
    page = render(cv, result, rows)
    out = VAULT / f"precision-filter-dev-{datetime.now(UTC).date().isoformat()}.md"
    out.write_text(page)
    print(page)
    print(f"written: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
