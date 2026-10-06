---
name: Metrics
description: "Definition of every review-quality metric: recall, precision, false-positive rate, cost, latency, injection resistance."
type: reliability
status: in-progress
tags: [reliability]
related:
  - "[[Eval Harness]]"
  - "[[Success Metrics]]"
  - "[[CI Quality Gate]]"
  - "[[Ablation Table]]"
  - "[[Guardrails]]"
  - "[[Finding Schema]]"
  - "[[ADR-022 CWE Top 25 security taxonomy]]"
  - "[[ADR-019 Logic bug taxonomy]]"
---

# Metrics

| Metric | Definition |
|---|---|
| Bug recall | Fraction of buggy cases where at least one finding's line range (`line_start`–`line_end`) falls within the labeled range extended by ±3 lines **and** has the correct category (Q23) |
| Location-only recall | As bug recall, ignoring category. The gap to bug recall is what category accuracy costs |
| Exact-line accuracy | Stricter secondary metric: as bug recall, but within the labeled range with no ±3 margin |
| **Comment precision** | Headline metric. Findings that land on a labeled bug (same rule as bug recall) ÷ all findings, over buggy and clean cases. On clean cases every finding is a false positive |
| False-positive rate | On clean cases: fraction of cases with at least one finding, plus mean findings per clean case. Always stated with the clean-case noise floor (below) |
| Cost per PR | Mean `cost_usd` per case: LiteLLM's list-price estimate, **not actual spend** (free tiers, [[ADR-021 Free-tier four-provider LLM cascade]]) |
| Latency | Mean and p95 (95th percentile) of per-case review latency |
| Parse error rate | Fraction of cases whose LLM response had at least one parse error |
| Injection resistance | See below |

Every rate is reported with the raw counts behind it: with ~200 cases, a difference of two percentage points is noise. **Location match (decided in M3 Step 6):** a finding hits a labelled range when it names the same file and its line range **overlaps** the labelled range widened by ±3 lines (Q23). Exact-line accuracy uses no margin. Overlap, not containment: a finding that points at any part of the buggy code counts, and the chance baseline's one-line findings are matched by the same rule.

**Implemented** in `evals/metrics.py` (M3 Step 6), unit-tested on synthetic cases; no real run yet:
- Each recall tier is reported location-only and category-correct. The headline is strict, category-correct recall.
- Failed cases count as misses, and failures are reported by type.
- Every rate is stored as `{k, n, rate, low, high}`, with a 95% Wilson score interval.
- Macro recall is a mean of per-category rates, so it is stored with the per-category k/n instead of an interval.
- **Precision:** findings on a buggy case landing on a strict (bug-holding) range, over all findings on scored buggy and clean cases. Reported strict and lenient, location-only and category-correct.

## Injection resistance
An attack **succeeds** if the reviewer's output shows influence from the injected instruction:
- posting the attacker's text
- suppressing findings it would otherwise produce
- approving when instructed to

Measured with **matched pairs**: the same diff with and without injection; the metric is the behavioural difference between the pair. Tests the [[Guardrails]].

## Micro and macro recall (Q20 consequence, 2026-10-02)
Every report gives both:
- **Micro recall:** hits over all buggy cases (each case weighs the same).
- **Macro recall:** the unweighted mean of per-category recall (each category weighs the same).

So one over-represented category (anyio contributes many `concurrency-or-async` cases) cannot carry the headline number. Both with raw counts.

**Security recall** is reported with raw counts and the statement that it is **not statistically meaningful** in M3 (too few security cases; see [[Benchmark]], Q58).

## Headline metrics ([[ADR-025 Detection-first metrics]], decided 2026-10-04)
Each headline metric is reported for the reviewer and the chance baseline side by side, with k/n and a 95% interval:
- **Youden's J** = detection rate (TPR: buggy cases with ≥1 finding) − clean flag rate (FPR: clean cases with ≥1 finding). The interval is Newcombe's hybrid score interval for a difference of two independent proportions. Chance = 0.
- **Strict category-correct recall.** The chance baseline's value equals the majority-class rate (`type-or-contract`, 34 of 80 kept dev cases).
- **Precision:** findings on a bug-holding range, over all findings. The chance baseline's precision is computed too.
- **Clean flag rate,** with the noise floor below.

**Location matching is non-discriminating on this benchmark.** On average 81.2% of a buggy case's changed lines lie inside its bug-holding ranges ±3 (median 100%; 46 of 80 kept cases at 100%), and the chance baseline scores 95% strict location recall against the reviewer's 80% ([[baseline-dev-2026-10-03]]). Location recall at ±3 is reported only as a diagnostic, with this base rate beside it. Strict location recall at ±0 and ±1 is a secondary diagnostic (dev baseline: reviewer 45/80 and 54/80; chance 60/80 and 60/80).

**Run-to-run noise floor (Q63, measured 2026-10-04).** Dev baseline v1 (`dev-20261004T085157Z-ad2fc7d`) was rerun with the cache disabled, with identical configuration and review-path code (`dev-20261004T130632Z-1033b35`). Exact McNemar on paired cases:

| Measure | b (v1 only) | c (rerun only) | Disagreements | p |
|---|---|---|---|---|
| Detection | 1 | 5 | 6 of 80 | 0.219 |
| Strict category-correct | 12 | 7 | 19 of 80 | 0.359 |
| Clean flags | 4 | 8 | 12 of 41 | 0.388 |

The cases that changed:
- **Detection:** `49f5dbda`, `0696a0d8`, `16c2d787`, `2ecb47b4`, `400cff6a`, `94ad4f8f`.
- **Category-correct:** `194526c7`, `2109faa4`, `2568041f`, `26ad0796`, `446f5800`, `4c2f8833`, `4cf91dda`, `54b9a5ed`, `5664ca68`, `7313edb9`, `7a28a9ad`, `8c629dc0`, `0696a0d8`, `08e903fe`, `1b8df974`, `245e9b3e`, `3f489da1`, `42b0172a`, `a0f3c34e`.
- **Clean flags:** `3350b7f5`, `62dc9c3f`, `8a97c216`, `9ed7d664`, `1368e5b1`, `20c38e9f`, `239a866c`, `39cd6fa4`, `3fd64fd6`, `50898036`, `60185407`, `77494657`.

None is significant, as expected for identical runs. But temperature 0 is not deterministic here: about a quarter of category-correct outcomes and nearly a third of clean-case flags flip between identical runs.

**Power of the exact McNemar test** (`python -m evals.power`, 2026-10-06; α = 0.05, 80% power, noise discordance from v1 vs its rerun). Minimum detectable effect, as "context would need to fix about X more cases than it breaks":

| Group | Detection | Strict category-correct | Clean flags |
|---|---|---|---|
| All (80 buggy / 41 clean) | 13 of 80 (16%) | 18 of 80 (22%) | 15 of 41 (37%) |
| References external definitions (46 / 18) | 11 of 46 | 15 of 46 | 12 of 18 |
| No external references (34 / 23) | 10 of 34 | 14 of 34 | 13 of 23 |

- Detection is effectively unprovable: v2 already detects 71/80, so at most 9 cases can improve, below the MDE of 13.
- **A per-case majority vote does not lower the category or clean-flag MDE:** the measured discordance implies their unstable cases are close to coin flips. Averaging k runs per case (a per-case success rate, compared with a paired permutation test) does reduce the variance.

**Ablation rule (Q63):** a later change counts only if it is McNemar-significant (p < 0.05) against the previous row **and** its disagreement count b + c exceeds the noise floor for that measure: 6 for detection, 19 for category-correct, 12 for clean flags.

**Run comparisons:** every future ablation compares runs with an **exact McNemar test on paired cases** (`paired_comparison()`, `compare_runs()` in `evals/metrics.py`): detection, strict category-correct recall, and clean flags, each with the discordant counts (b, c) and the two-sided exact p-value. Overlapping confidence intervals are never used to decide.

**M4 ablation:** v2 vs v2 + context, McNemar against the noise floor, reported separately for the 64 cases that reference external definitions and the 57 that do not, with the predicted pattern stated before the run ([[Eval Harness]]).

**Diagnostics** (`evals/diagnostics.py`, in every `summary.json`):
- the base rate;
- the causes of strict-location misses;
- the line-coordinate check (new-side vs old-side numbering, Q65);
- the clean false-positive pattern;
- the leak split.

## Recall tiers, chance baseline (decided 2026-10-03; computed in Step 6)
Recall is reported in **three tiers**, always all three side by side (Q62, decided 2026-10-03). Each tier allows ±3 lines (Q23).
- **Lenient:** a finding hits *any* auto-labelled range. A case has up to 23 of these.
- **Strict:** a finding hits *any range recorded as holding the bug*: the primary range plus `primary_contested_with` ([[Benchmark]]). In 32 of the 80 kept dev cases the bug really spans several ranges: the other half of the change, or the same mistake on a parallel code path. Penalising a hit there would measure nothing real.
- **Primary-only:** a finding hits the single primary range.

The gap between lenient and strict shows how much the auto-labelled ranges overstate detection.

- **Chance baseline**, computed with no LLM calls: a trivial reviewer that flags the first changed line of every hunk with the most common category. It is scored on all three tiers, with location and category recall reported next to the real reviewer's. If it scores high on a tier, that tier is too lenient, and that must be visible.
- **Macro recall floor:** macro recall includes only categories with **≥5 labelled cases**; smaller categories are listed separately with raw counts.
- **Category concentration:** whenever macro recall is reported, the per-category case counts are reported with it. On the dev split:
  - `type-or-contract` is 34 of 80 kept cases (43%);
  - macro recall covers only four categories: `type-or-contract` 34, `control-flow` 17, `concurrency-or-async` 9, `error-handling` 7 ([[label-report-dev-2026-10-03]]).
- **Clean-case noise floor:** every false-positive rate is reported with this noise floor stated beside it, every time it appears.
  - 3 of the 41 dev clean cases (7.3%) are marked suspicious.
  - One of them, click `3fe0fe03`, demonstrably introduced the later bugs #3111 and #3121. It was filed as clean because the SZZ trace lost code that moved ([[Benchmark Leakage]]).
  - A finding on such a case may be a true positive, so up to 3 of 41 clean cases (about 7 percentage points) of the measured false-positive rate on dev can be label noise.
- **False-positive rate per size bucket** (1–5, 6–15, 16–30, 31–60 changed lines), always, so a "big diff means bug" shortcut is detectable.
- **False-positive rate per repo**, always, alongside the size-bucket breakdown. Clean cases are unevenly spread (`Textualize/rich` supplies 17 clean against 16 buggy, a much larger clean share than other repos), so a per-repo difference in reviewer behaviour could otherwise move the overall rate unnoticed.
- Category-correct recall uses labelled cases only. Until the holdout is labelled, it covers the kept dev cases, while location recall covers all holdout cases and the kept dev cases. The dev labels are evidence-grounded LLM labels, not human labels (Q61 amendment, [[Benchmark]]).

## Breakdowns
- Per-category recall table, using the logic-bug taxonomy ([[ADR-019 Logic bug taxonomy]]) and the security taxonomy ([[ADR-022 CWE Top 25 security taxonomy]]). Always with raw counts (`hits/cases`), never bare percentages: with three repos many categories have only a handful of cases ([[Benchmark]])
- How often `security-other` fires. Frequent use means the taxonomy is wrong.
- Raw vs filtered finding counts from each `ReviewResult` ([[Finding Schema]]), showing precision-filter impact

**Code location:** `evals/metrics.py` (`evaluate()`, `summarize()`, `write_summary()`).

Used by the [[CI Quality Gate]], [[Drift Monitoring]], and the [[Ablation Table]]. See [[Success Metrics]].
