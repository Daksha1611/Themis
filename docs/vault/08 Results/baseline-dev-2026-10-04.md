---
name: baseline-dev-2026-10-04
description: "Baseline eval of the dev split on the pinned model: Youden's J, category-correct recall, precision, clean flag rate, chance baseline, diagnostics, caveats."
type: reliability
status: done
tags: [reliability, results]
related:
  - "[[Metrics]]"
  - "[[Benchmark]]"
  - "[[Eval Harness]]"
  - "[[ADR-025 Detection-first metrics]]"
  - "[[label-report-dev-2026-10-03]]"
---

# Baseline: dev split, groq/openai/gpt-oss-120b

- Run: `dev-20261004T085157Z-ad2fc7d` (git `ad2fc7d`), finished 2026-10-04T08:55:00+00:00
- Pinned model ([[ADR-024 Eval runs pin a single provider and model]]): `groq/openai/gpt-oss-120b`, temperature 0.0, max_tokens 2048
- Scored cases: 80 kept buggy + 41 clean; case order shuffled with seed 20261003
- Diff transform: `mask-issue-refs-v1` (issue references in removed lines masked; [[Benchmark]])
- **This baseline includes a masked rerun:** 7 cases whose diffs the transform changed were called fresh (`0696a0d863b0b8fe`, `1febecd36c0d6c24`, `2e327bebc7bbf91b`, `472aeb4f89993281`, `4f9af0ec1c05847f`, `60ce72ccf8b5f05e`, `a3e5f5b90622d8e2`); the other 114 came from the response cache, unchanged.
- Raw evidence: `evals/results/dev-20261004T085157Z-ad2fc7d/` (`results.jsonl`, `summary.json`)

## Headline (ADR-025)

| Metric | Reviewer | Chance baseline |
|---|---|---|
| **Youden's J** = detection rate − clean flag rate | **0.435 (95% CI 0.257 to 0.586)** | 0.000 (95% CI -0.046 to 0.086) |
| **Strict category-correct recall** | **51.2% (41/80; 95% CI 40.5%–61.9%)** | 42.5% (34/80; 95% CI 32.3%–53.4%) |
| **Precision** (findings on a bug-holding range) | **68.5% (74/108; 95% CI 59.3%–76.5%)** | 38.7% (94/243; 95% CI 32.8%–44.9%) |
| **Clean flag rate** (FPR) | **41.5% (17/41; 95% CI 27.8%–56.6%)** | 100.0% (41/41; 95% CI 91.4%–100.0%) |
| Detection rate (TPR) | 85.0% (68/80; 95% CI 75.6%–91.2%) | 100.0% (80/80; 95% CI 95.4%–100.0%) |

- The chance baseline flags the first changed line of every hunk of every case as `type-or-contract`. It detects every case and flags every clean case, so its J is 0. Its category-correct recall equals the majority-class rate: the share of kept buggy cases labelled `type-or-contract`.
- Clean flag rate noise floor: 3 of 41 dev clean cases (7.3%) are marked suspicious, so up to that share of the clean flag rate may be label noise.

## Location matching: a diagnostic, not a headline

**Location recall at ±3 lines is non-discriminating on this benchmark:** on average 81.2% of a buggy case's changed lines lie inside its bug-holding ranges ±3 (median 100%; 46 of 80 cases at 100%). A reviewer that points anywhere in the diff lands on a labelled range, so the chance baseline scores higher than the reviewer.

| Strict location recall | Reviewer | Chance baseline |
|---|---|---|
| ±0 lines | 55.0% (44/80; 95% CI 44.1%–65.4%) | 75.0% (60/80; 95% CI 64.5%–83.2%) |
| ±1 lines | 66.2% (53/80; 95% CI 55.4%–75.7%) | 75.0% (60/80; 95% CI 64.5%–83.2%) |
| ±3 lines | 78.8% (63/80; 95% CI 68.6%–86.3%) | 95.0% (76/80; 95% CI 87.8%–98.0%) |

| Tier | Mode | Reviewer | Chance baseline |
|---|---|---|---|
| Lenient (any auto-labelled range) | location-only ⚠ | 81.2% (65/80; 95% CI 71.3%–88.3%) | 100.0% (80/80; 95% CI 95.4%–100.0%) |
| Lenient (any auto-labelled range) | category-correct | 53.8% (43/80; 95% CI 42.9%–64.3%) | 42.5% (34/80; 95% CI 32.3%–53.4%) |
| Strict (bug-holding ranges) | location-only ⚠ | 78.8% (63/80; 95% CI 68.6%–86.3%) | 95.0% (76/80; 95% CI 87.8%–98.0%) |
| Strict (bug-holding ranges) | category-correct | 51.2% (41/80; 95% CI 40.5%–61.9%) | 42.5% (34/80; 95% CI 32.3%–53.4%) |
| Primary-only | location-only ⚠ | 76.2% (61/80; 95% CI 65.9%–84.2%) | 88.8% (71/80; 95% CI 80.0%–94.0%) |
| Primary-only | category-correct | 51.2% (41/80; 95% CI 40.5%–61.9%) | 40.0% (32/80; 95% CI 30.0%–51.0%) |

⚠ location-only rows are non-discriminating at ±3 (base rate above).

## Micro and macro recall (strict, category-correct)

- Micro: 51.2% (41/80; 95% CI 40.5%–61.9%)
- Macro over categories with ≥5 kept cases: 0.507 (a mean of per-category rates; counts below)

| Category | Cases | Strict category-correct | Chance | Macro |
|---|---|---|---|---|
| type-or-contract | 34 | 52.9% (18/34; 95% CI 36.7%–68.5%) | 100.0% (34/34; 95% CI 89.8%–100.0%) | yes |
| control-flow | 17 | 70.6% (12/17; 95% CI 46.9%–86.7%) | 0.0% (0/17; 95% CI 0.0%–18.4%) | yes |
| concurrency-or-async | 9 | 22.2% (2/9; 95% CI 6.3%–54.7%) | 0.0% (0/9; 95% CI 0.0%–29.9%) | yes |
| error-handling | 7 | 57.1% (4/7; 95% CI 25.0%–84.2%) | 0.0% (0/7; 95% CI 0.0%–35.4%) | yes |
| null-or-none-handling | 4 | 75.0% (3/4; 95% CI 30.1%–95.4%) | 0.0% (0/4; 95% CI 0.0%–49.0%) | no (below floor) |
| off-by-one-or-boundary | 3 | 0.0% (0/3; 95% CI 0.0%–56.2%) | 0.0% (0/3; 95% CI 0.0%–56.2%) | no (below floor) |
| arithmetic-or-numeric | 2 | 0.0% (0/2; 95% CI 0.0%–65.8%) | 0.0% (0/2; 95% CI 0.0%–65.8%) | no (below floor) |
| resource-leak | 2 | 100.0% (2/2; 95% CI 34.2%–100.0%) | 0.0% (0/2; 95% CI 0.0%–65.8%) | no (below floor) |
| CWE-20 | 1 | 0.0% (0/1; 95% CI 0.0%–79.3%) | 0.0% (0/1; 95% CI 0.0%–79.3%) | no (below floor) |
| CWE-400 | 1 | 0.0% (0/1; 95% CI 0.0%–79.3%) | 0.0% (0/1; 95% CI 0.0%–79.3%) | no (below floor) |

## Clean cases

Every rate here carries the clean-case noise floor: 3 of 41 dev clean cases (7.3%) are marked suspicious, so up to that share of the clean flag rate may be label noise.

- Clean flag rate: 41.5% (17/41; 95% CI 27.8%–56.6%); mean findings per clean case 0.49. Chance baseline: 100.0% (41/41; 95% CI 91.4%–100.0%).

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

**False-positive pattern** (20 findings on 17 clean cases): by category {'type-or-contract': 11, 'control-flow': 4, 'off-by-one-or-boundary': 2, 'null-or-none-handling': 1, 'concurrency-or-async': 1, 'CWE-20': 1}; by severity {'medium': 14, 'low': 3, 'high': 3}; flagged by size {'1-5': '7/17', '16-30': '6/8', '31-60': '0/3', '6-15': '4/13'}; by repo {'Textualize/rich': '3/10', 'agronholm/anyio': '4/8', 'fastapi/fastapi': '6/11', 'marshmallow-code/marshmallow': '0/2', 'pallets/click': '4/10'}. Suspicious clean cases flagged: `3350b7f5558de194`, `3fe0fe03cd5c9e75` (possibly true positives; see the label report).

## Recall by repo and by size (strict, category-correct)

| Group | Recall |
|---|---|
| repo Textualize/rich | 42.9% (3/7; 95% CI 15.8%–75.0%) |
| repo agronholm/anyio | 44.0% (11/25; 95% CI 26.7%–62.9%) |
| repo fastapi/fastapi | 73.9% (17/23; 95% CI 53.5%–87.5%) |
| repo marshmallow-code/marshmallow | 25.0% (2/8; 95% CI 7.1%–59.1%) |
| repo pallets/click | 47.1% (8/17; 95% CI 26.2%–69.0%) |
| size 1-5 lines | 60.0% (18/30; 95% CI 42.3%–75.4%) |
| size 16-30 lines | 37.5% (6/16; 95% CI 18.5%–61.4%) |
| size 31-60 lines | 40.0% (4/10; 95% CI 16.8%–68.7%) |
| size 6-15 lines | 54.2% (13/24; 95% CI 35.1%–72.1%) |

## Diagnostics

**Strict-location misses: 17.**

- findings cite removed lines by old-file number: 2 (`a3e5f5b90622d8e2`, `2106f137b8772e1c`)
- findings on changed lines, outside the ±3 window: 2 (`08e903fe777a642c`, `49f5dbda529ea26b`)
- findings outside the diff: 1 (`3f489da11486b473`)
- no findings: 11 (`7ec3ae5c5e31d3a2`, `24517970965f73df`, `514024d672807316`, `400cff6a304c125b`, `2ecb47b433d60707`, `8d2bb2c2fcb58432`, `4ffca0ce378367c6`, `16c2d787b571890c`, `94ad4f8fb317b04e`, `c3ee72768a1488f2`, `0696a0d863b0b8fe`)
- no usable answer (failed:parse): 1 (`1182525f5df99d56`)

**Line coordinates** (108 findings): {'new-side, on an added line': 58, 'ambiguous: new-side context or old-side removed line': 24, 'new-side, context line': 15, 'old-side only: cites a removed line by its old-file number': 7, 'outside the diff on both sides': 4}. Most findings use new-file lines, as the labels do. A few cite removed lines by their old-file numbers, a convention the prompt does not set (Q65).

**Leak split** (cases whose removed lines matched the leak scan vs the rest):

- leak-scan matches (9): detection 88.9% (8/9; 95% CI 56.5%–98.0%); strict category-correct 33.3% (3/9; 95% CI 12.1%–64.6%)
- others (71): detection 84.5% (60/71; 95% CI 74.3%–91.1%); strict category-correct 53.5% (38/71; 95% CI 42.0%–64.6%)

**Paired comparison with `dev-20261003T122301Z-86166c4`** (exact McNemar):

- detected: b = 1 (earlier only), c = 0 (this run only), 80 pairs, p = 1.000
- strict_category: b = 1 (earlier only), c = 1 (this run only), 80 pairs, p = 1.000
- flagged: b = 0 (earlier only), c = 0 (this run only), 41 pairs, p = 1.000

## Security

Raw counts only; **not statistically meaningful** (too few cases, Q58): CWE-20 0/1, CWE-400 0/1.

## Operations

- Cases answered: 121/121; status: {'failed:parse': 1, 'partial': 2, 'success': 118}
- Failures by type: {'failed:parse': 1}
- Parse-error rate: 2.5% (3/121; 95% CI 0.8%–7.0%)
- Cost: mean 0.00057 USD per case, total 0.0689 USD (LiteLLM list-price estimate; actual free-tier spend is $0)
- Latency: mean 2300 ms, p95 4815 ms (original call latency, also for cached cases)
- Tokens: prompt 132645, completion 86619
- Cache: 94.2% (114/121; 95% CI 88.5%–97.2%) cases served from cache; provider attempts 7
- Provider/model of answered cases: {'groq/openai/gpt-oss-120b': 121}; pinned-model share 100.0% (121/121; 95% CI 96.9%–100.0%); identical model ID across sessions: True

## Caveats

- ⚠ Failed cases count as misses: {'failed:parse': 1}.
- **Location matching is non-discriminating on this benchmark:** on average 81.2% of a buggy case's changed lines lie inside its bug-holding ranges ±3 (median 100%; 46 of 80 cases at 100%). Location recall at ±3 is reported as a diagnostic only ([[ADR-025 Detection-first metrics]]).
- **Labels:** LLM-assigned from human-written upstream evidence. The owner verified them on a 28-case sample (25 stratified + 3 borderline): 25/25 agreement per field (95% lower bound 86.7%) ([[label-report-dev-2026-10-03]], [[Benchmark]]).
- **Clean-case noise floor: 3 of 41 dev clean cases (7.3%) are marked suspicious, so up to that share of the clean flag rate may be label noise.** Two of the three suspicious cases were flagged; one (click `3fe0fe03`) demonstrably introduced later bugs, and SZZ missed it because the code moved ([[Benchmark Leakage]]).
- **Category concentration:** `type-or-contract` is 34 of 80 kept cases (43%), which is also the chance baseline's category-correct recall. Macro recall covers only four categories, with the counts shown beside it.
- **Security is not measurable** here: 2 kept security cases.
- **Leakage profile:** 92% of buggy cases are after mid-2025; `Textualize/rich` has the weakest date profile ([[Benchmark Leakage]]). Issue references in removed lines are masked (`mask-issue-refs-v1`).
- **Single run:** run-to-run variance is not measured yet (Q63). The masked cases are fresh samples, so part of any change on them is that variance.
- **Diff-only review:** every eval case gets a neutral PR title to prevent label leakage; production passes the real title, so production performance may differ ([[Eval Harness]]).
- **Line-coordinate convention (Q65):** findings about removed code sometimes cite old-file line numbers; labels use new-file lines.
