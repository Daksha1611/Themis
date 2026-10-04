---
name: baseline-dev-2026-10-03
description: "Baseline eval of the dev split on the pinned model: recall tiers, precision, false positives, chance baseline, caveats."
type: reliability
status: done
tags: [reliability, results]
related:
  - "[[Metrics]]"
  - "[[Benchmark]]"
  - "[[Eval Harness]]"
  - "[[label-report-dev-2026-10-03]]"
---

> **Superseded by [[baseline-dev-2026-10-04]]** ([[ADR-025 Detection-first metrics]]). This report is kept as written. Its headline relied on location matching, which turned out to be non-discriminating on this benchmark (the chance baseline scored higher). The run itself is unchanged and still valid evidence.

# Baseline: dev split, groq/openai/gpt-oss-120b

- Run: `dev-20261003T122301Z-86166c4` (git `86166c4`), finished 2026-10-03T13:23:24+00:00
- Pinned model ([[ADR-024 Eval runs pin a single provider and model]]): `groq/openai/gpt-oss-120b`, temperature 0.0, max_tokens 2048
- Scored cases: 80 kept buggy + 41 clean; case order shuffled with seed 20261003
- Location match: same file, line ranges overlap, ±3 lines ([[Metrics]])
- Raw evidence: `evals/results/dev-20261003T122301Z-86166c4/` (`results.jsonl`, `summary.json`)

## Headline

- **Strict, category-correct recall:** 51.2% (41/80; 95% CI 40.5%–61.9%)
- **Precision (strict, location):** 68.8% (75/109; 95% CI 59.6%–76.7%)
- **False-positive rate on clean cases:** 41.5% (17/41; 95% CI 27.8%–56.6%); noise floor: 3 of 41 dev clean cases (7.3%) are marked suspicious, so up to that share of the false-positive rate may be label noise

## Recall: three tiers, two matching modes, against the chance baseline

The chance baseline flags the first changed line of every hunk as `type-or-contract` (no LLM).

| Tier | Mode | Reviewer | Chance baseline |
|---|---|---|---|
| Lenient (any auto-labelled range) | location-only | 82.5% (66/80; 95% CI 72.7%–89.3%) | 100.0% (80/80; 95% CI 95.4%–100.0%) |
| Lenient (any auto-labelled range) | category-correct | 53.8% (43/80; 95% CI 42.9%–64.3%) | 42.5% (34/80; 95% CI 32.3%–53.4%) |
| Strict (bug-holding ranges) | location-only | 80.0% (64/80; 95% CI 70.0%–87.3%) | 95.0% (76/80; 95% CI 87.8%–98.0%) |
| Strict (bug-holding ranges) | category-correct | 51.2% (41/80; 95% CI 40.5%–61.9%) | 42.5% (34/80; 95% CI 32.3%–53.4%) |
| Primary-only | location-only | 77.5% (62/80; 95% CI 67.2%–85.3%) | 88.8% (71/80; 95% CI 80.0%–94.0%) |
| Primary-only | category-correct | 51.2% (41/80; 95% CI 40.5%–61.9%) | 40.0% (32/80; 95% CI 30.0%–51.0%) |

Exact-line (strict ranges, no margin): location 56.2% (45/80; 95% CI 45.3%–66.6%); category-correct 38.8% (31/80; 95% CI 28.8%–49.7%).

## Micro and macro recall (strict)

- Micro, category-correct: 51.2% (41/80; 95% CI 40.5%–61.9%)
- Macro over categories with ≥5 kept cases: category-correct 0.515, location 0.821 (a mean of per-category rates; counts below)

| Category | Cases | Strict location | Strict category-correct | Macro |
|---|---|---|---|---|
| type-or-contract | 34 | 73.5% (25/34; 95% CI 56.9%–85.4%) | 55.9% (19/34; 95% CI 39.5%–71.1%) | yes |
| control-flow | 17 | 88.2% (15/17; 95% CI 65.7%–96.7%) | 70.6% (12/17; 95% CI 46.9%–86.7%) | yes |
| concurrency-or-async | 9 | 66.7% (6/9; 95% CI 35.4%–87.9%) | 22.2% (2/9; 95% CI 6.3%–54.7%) | yes |
| error-handling | 7 | 100.0% (7/7; 95% CI 64.6%–100.0%) | 57.1% (4/7; 95% CI 25.0%–84.2%) | yes |
| null-or-none-handling | 4 | 100.0% (4/4; 95% CI 51.0%–100.0%) | 50.0% (2/4; 95% CI 15.0%–85.0%) | no (below floor) |
| off-by-one-or-boundary | 3 | 66.7% (2/3; 95% CI 20.8%–93.9%) | 0.0% (0/3; 95% CI 0.0%–56.2%) | no (below floor) |
| arithmetic-or-numeric | 2 | 100.0% (2/2; 95% CI 34.2%–100.0%) | 0.0% (0/2; 95% CI 0.0%–65.8%) | no (below floor) |
| resource-leak | 2 | 100.0% (2/2; 95% CI 34.2%–100.0%) | 100.0% (2/2; 95% CI 34.2%–100.0%) | no (below floor) |
| CWE-20 | 1 | 100.0% (1/1; 95% CI 20.7%–100.0%) | 0.0% (0/1; 95% CI 0.0%–79.3%) | no (below floor) |
| CWE-400 | 1 | 0.0% (0/1; 95% CI 0.0%–79.3%) | 0.0% (0/1; 95% CI 0.0%–79.3%) | no (below floor) |

## Precision

109 findings in all, 20 on clean cases (chance baseline: 243, 89).

| Precision | Reviewer | Chance baseline |
|---|---|---|
| strict, location | 68.8% (75/109; 95% CI 59.6%–76.7%) | 38.7% (94/243; 95% CI 32.8%–44.9%) |
| strict, category | 41.3% (45/109; 95% CI 32.5%–50.7%) | 18.1% (44/243; 95% CI 13.8%–23.4%) |
| lenient, location | 72.5% (79/109; 95% CI 63.4%–80.0%) | 63.4% (154/243; 95% CI 57.2%–69.2%) |
| lenient, category | 44.0% (48/109; 95% CI 35.1%–53.4%) | 26.3% (64/243; 95% CI 21.2%–32.2%) |

## False positives on clean cases

Every rate here carries the clean-case noise floor: 3 of 41 dev clean cases (7.3%) are marked suspicious, so up to that share of the false-positive rate may be label noise.

- Overall: 41.5% (17/41; 95% CI 27.8%–56.6%) of clean cases have ≥1 finding; mean findings per clean case 0.49. Chance baseline: 100.0% (41/41; 95% CI 91.4%–100.0%).

| Group | Clean cases with ≥1 finding | Mean findings |
|---|---|---|
| size 1-5 | 41.2% (7/17; 95% CI 21.6%–64.0%) | 0.47 |
| size 16-30 | 75.0% (6/8; 95% CI 40.9%–92.9%) | 1.00 |
| size 31-60 | 0.0% (0/3; 95% CI 0.0%–56.2%) | 0.00 |
| size 6-15 | 30.8% (4/13; 95% CI 12.7%–57.6%) | 0.31 |
| repo Textualize/rich | 30.0% (3/10; 95% CI 10.8%–60.3%) | 0.40 |
| repo agronholm/anyio | 50.0% (4/8; 95% CI 21.5%–78.5%) | 0.50 |
| repo fastapi/fastapi | 54.5% (6/11; 95% CI 28.0%–78.7%) | 0.64 |
| repo marshmallow-code/marshmallow | 0.0% (0/2; 95% CI 0.0%–65.8%) | 0.00 |
| repo pallets/click | 40.0% (4/10; 95% CI 16.8%–68.7%) | 0.50 |

## Strict category-correct recall by repo and by size

| Group | Recall |
|---|---|
| repo Textualize/rich | 42.9% (3/7; 95% CI 15.8%–75.0%) |
| repo agronholm/anyio | 44.0% (11/25; 95% CI 26.7%–62.9%) |
| repo fastapi/fastapi | 73.9% (17/23; 95% CI 53.5%–87.5%) |
| repo marshmallow-code/marshmallow | 25.0% (2/8; 95% CI 7.1%–59.1%) |
| repo pallets/click | 47.1% (8/17; 95% CI 26.2%–69.0%) |
| size 1-5 lines | 60.0% (18/30; 95% CI 42.3%–75.4%) |
| size 16-30 lines | 43.8% (7/16; 95% CI 23.1%–66.8%) |
| size 31-60 lines | 30.0% (3/10; 95% CI 10.8%–60.3%) |
| size 6-15 lines | 54.2% (13/24; 95% CI 35.1%–72.1%) |

## Security

Raw counts only; **not statistically meaningful** (too few cases, Q58): CWE-20 0/1, CWE-400 0/1.

## Operations

- Cases answered: 121/121; status: {'failed:parse': 1, 'partial': 1, 'success': 119}
- Failures by type: {'failed:parse': 1}
- Parse-error rate: 1.7% (2/121; 95% CI 0.5%–5.8%)
- Cost: mean 0.00057 USD per case, total 0.0689 USD (LiteLLM list-price estimate; actual free-tier spend is $0)
- Latency: mean 2321 ms, p95 4815 ms (original call latency, also for cached cases)
- Tokens: prompt 132719, completion 86892; estimated prompt tokens 125635 vs actual 132719 on answered cases
- Cache: 0.0% (0/121; 95% CI 0.0%–3.1%) cases served from cache; provider attempts 122
- Provider/model of answered cases: {'groq/openai/gpt-oss-120b': 121}; pinned-model share 100.0% (121/121; 95% CI 96.9%–100.0%)

## Schedule

| Session | Started | Ended | Stop | Cases |
|---|---|---|---|---|
| 1 | 2026-10-03T12:23:01+00:00 | 2026-10-03T13:23:24+00:00 | complete | 121 |

Cases per UTC day: 2026-10-03 121. Model identifiers per session: {'1': {'groq/openai/gpt-oss-120b': 121}}.

## Caveats

- ⚠ Failed cases count as misses: {'failed:parse': 1}.
- **Labels:** LLM-assigned from human-written upstream evidence. The owner verified them on a 28-case sample (25 stratified + 3 borderline): 25/25 agreement per field (95% lower bound 86.7%) ([[label-report-dev-2026-10-03]], [[Benchmark]]).
- **Clean-case noise floor: 3 of 41 dev clean cases (7.3%) are marked suspicious, so up to that share of the false-positive rate may be label noise.** One suspicious case (click `3fe0fe03`) demonstrably introduced later bugs; SZZ missed it because the code moved ([[Benchmark Leakage]]).
- **Category concentration:** `type-or-contract` is 34 of 80 kept cases (43%); macro recall covers only four categories, with the counts shown beside it.
- **Security is not measurable** here: 2 kept security cases.
- **Leakage profile:** 92% of buggy cases are after mid-2025; `Textualize/rich` has the weakest date profile ([[Benchmark Leakage]]).
- **Single run:** run-to-run variance is not measured yet (Q63).
- **Diff-only review:** every eval case gets a neutral PR title to prevent label leakage; production passes the real title, so production performance may differ ([[Eval Harness]]).
- **Leak scan:** 9 of 80 buggy diffs (and 2 of 41 clean) have issue references or telltale words in their removed lines, mostly comments citing the fixed issue; not changed pending the owner's decision ([[Benchmark]]).
