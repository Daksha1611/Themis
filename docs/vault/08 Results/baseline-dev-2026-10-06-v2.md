---
name: baseline-dev-2026-10-06-v2
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

- Run: `dev-20261004T140940Z-4feea8e` (git `4feea8e`), finished 2026-10-06T06:33:25+00:00
- Pinned model ([[ADR-024 Eval runs pin a single provider and model]]): `groq/openai/gpt-oss-120b`, temperature 0.0, max_tokens 2048
- Scored cases: 80 kept buggy + 41 clean; case order shuffled with seed 20261003
- Diff transform: `mask-issue-refs-v1` (issue references in removed lines masked; [[Benchmark]])
- **This baseline includes a masked rerun:** 7 cases whose diffs the transform changed were called fresh (`0696a0d863b0b8fe`, `1febecd36c0d6c24`, `2e327bebc7bbf91b`, `472aeb4f89993281`, `4f9af0ec1c05847f`, `60ce72ccf8b5f05e`, `a3e5f5b90622d8e2`); the other 114 came from the response cache, unchanged.
- Raw evidence: `evals/results/dev-20261004T140940Z-4feea8e/` (`results.jsonl`, `summary.json`)

## Headline (ADR-025)

| Metric | Reviewer | Chance baseline |
|---|---|---|
| **Youden's J** = detection rate − clean flag rate | **0.327 (95% CI 0.161 to 0.486)** | 0.000 (95% CI -0.046 to 0.086) |
| **Strict category-correct recall** | **51.2% (41/80; 95% CI 40.5%–61.9%)** | 42.5% (34/80; 95% CI 32.3%–53.4%) |
| **Precision** (findings on a bug-holding range) | **66.9% (83/124; 95% CI 58.3%–74.6%)** | 38.7% (94/243; 95% CI 32.8%–44.9%) |
| **Clean flag rate** (FPR) | **56.1% (23/41; 95% CI 41.0%–70.1%)** | 100.0% (41/41; 95% CI 91.4%–100.0%) |
| Detection rate (TPR) | 88.8% (71/80; 95% CI 80.0%–94.0%) | 100.0% (80/80; 95% CI 95.4%–100.0%) |

- The chance baseline flags the first changed line of every hunk of every case as `type-or-contract`. It detects every case and flags every clean case, so its J is 0. Its category-correct recall equals the majority-class rate: the share of kept buggy cases labelled `type-or-contract`.
- Clean flag rate noise floor: 3 of 41 dev clean cases (7.3%) are marked suspicious, so up to that share of the clean flag rate may be label noise.

## Runs side by side

| Metric | v1 | v1 rerun | v2 | Chance baseline |
|---|---|---|---|---|
| Youden's J | 0.435 (95% CI 0.257 to 0.586) | 0.388 (95% CI 0.219 to 0.543) | 0.327 (95% CI 0.161 to 0.486) | 0.000 (95% CI -0.046 to 0.086) |
| Strict category-correct recall | 51.2% (41/80; 95% CI 40.5%–61.9%) | 45.0% (36/80; 95% CI 34.6%–55.9%) | 51.2% (41/80; 95% CI 40.5%–61.9%) | 42.5% (34/80; 95% CI 32.3%–53.4%) |
| Precision | 68.5% (74/108; 95% CI 59.3%–76.5%) | 63.2% (74/117; 95% CI 54.2%–71.4%) | 66.9% (83/124; 95% CI 58.3%–74.6%) | 38.7% (94/243; 95% CI 32.8%–44.9%) |
| Clean flag rate | 41.5% (17/41; 95% CI 27.8%–56.6%) | 51.2% (21/41; 95% CI 36.5%–65.7%) | 56.1% (23/41; 95% CI 41.0%–70.1%) | 100.0% (41/41; 95% CI 91.4%–100.0%) |
| Detection rate | 85.0% (68/80; 95% CI 75.6%–91.2%) | 90.0% (72/80; 95% CI 81.5%–94.8%) | 88.8% (71/80; 95% CI 80.0%–94.0%) | 100.0% (80/80; 95% CI 95.4%–100.0%) |
| Parse failures | {'failed:parse': 1} | {'failed:parse': 2, 'failed:provider-error': 1} | none | — |
| Validation retries | 0 | 0 | 4 | — |
| Invalid-line findings dropped | 0 | 0 | 2 | — |
| Mean cost per case (list-price estimate) | 0.00057 USD | 0.00060 USD | 0.00065 USD | — |
| p95 latency | 4.8 s | 4.7 s | 5.2 s | — |

## Run-to-run noise floor (Q63)

Two runs with identical configuration and review code (v1 vs v1 rerun; the second with the cache disabled), exact McNemar on paired cases:

- Detection (buggy cases with ≥1 finding): b = 1, c = 5, p = 0.219; disagreements 6 of 80 (`49f5dbda529ea26b`, `0696a0d863b0b8fe`, `16c2d787b571890c`, `2ecb47b433d60707`, `400cff6a304c125b`, `94ad4f8fb317b04e`)
- Strict category-correct: b = 12, c = 7, p = 0.359; disagreements 19 of 80 (`194526c7337634d7`, `2109faa46125df3d`, `2568041febc6d104`, `26ad079673af9382`, `446f5800db554d12`, `4c2f88339677cd86`, `4cf91dda2d9a58e3`, `54b9a5edb3e0b3e5`, `5664ca68e610b908`, `7313edb9e374be2d`, `7a28a9adf0d7d761`, `8c629dc0a90265b9`, `0696a0d863b0b8fe`, `08e903fe777a642c`, `1b8df9743a9872e2`, `245e9b3e56783615`, `3f489da11486b473`, `42b0172a905fe7e4`, `a0f3c34e0be57622`)
- Clean flag (clean cases with ≥1 finding): b = 4, c = 8, p = 0.388; disagreements 12 of 41 (`3350b7f5558de194`, `62dc9c3f5126f706`, `8a97c216e28edb90`, `9ed7d664a569e506`, `1368e5b14e17732e`, `20c38e9f71d460b5`, `239a866ce1f91049`, `39cd6fa4ec358034`, `3fd64fd644e3e89e`, `5089803ebaf4be59`, `6018540745d6183d`, `77494657c8dc1856`)

**Rule:** a later change counts only if it is McNemar-significant (p < 0.05) against the previous row **and** its disagreement count (b + c) exceeds the noise floor above.

## v1 → v2 (exact McNemar)

- Detection (buggy cases with ≥1 finding): b = 2 (v1 only), c = 5 (v2 only), p = 0.453: not significant
- Strict category-correct: b = 8 (v1 only), c = 8 (v2 only), p = 1.000: not significant
- Clean flag (clean cases with ≥1 finding): b = 2 (v1 only), c = 8 (v2 only), p = 0.109: not significant

**Attribution of the 30 cases whose outcome changed** (any field; no extra calls). Retry-related: v2 needed a validation retry. Numbering-related: v1 had a finding citing an old-file line or pointing outside the diff.

| Group | Cases | Case IDs |
|---|---|---|
| retry-related | 4 | `1182525f5df99d56`, `239a866ce1f91049`, `245e9b3e56783615`, `49f5dbda529ea26b` |
| numbering-related | 2 | `2106f137b8772e1c`, `3f489da11486b473` |
| both | 0 | — |
| neither | 24 | `0696a0d863b0b8fe`, `1368e5b14e17732e`, `16c2d787b571890c`, `1b8df9743a9872e2`, `1febecd36c0d6c24`, `20c38e9f71d460b5`, `2109faa46125df3d`, `26ad079673af9382`, `2ecb47b433d60707`, `36b1a3b76394efc3`, `3fd64fd644e3e89e`, `42b0172a905fe7e4`, `480ba4bc4eff750a`, `4cf91dda2d9a58e3`, `5089803ebaf4be59`, `54b9a5edb3e0b3e5`, `5dd6a5f8d949c1df`, `6018540745d6183d`, `7ec3ae5c5e31d3a2`, `8a97c216e28edb90`, `953384b97cf8b26e`, `97ba9f5a10b0a4ec`, `9ed7d664a569e506`, `d777dbbda423e6fc` |

Cases in "neither" (24) are most likely run-to-run variance; two identical runs changed 36 cases on the same fields (noise floor).

## Sensitivity line (suspicious clean cases excluded)

Excluding the 3 clean cases marked suspicious during labelling, a criterion recorded before any results were seen. Headline numbers stay on the full frozen set.

| Run | Clean flag rate | Precision | J |
|---|---|---|---|
| v1 | 39.5% (15/38; 95% CI 25.6%–55.3%) | 70.5% (74/105; 95% CI 61.2%–78.4%) | 0.455 (95% CI 0.271 to 0.607) |
| v1 rerun | 50.0% (19/38; 95% CI 34.8%–65.2%) | 64.3% (74/115; 95% CI 55.3%–72.5%) | 0.400 (95% CI 0.226 to 0.559) |
| v2 | 52.6% (20/38; 95% CI 37.3%–67.5%) | 68.6% (83/121; 95% CI 59.9%–76.2%) | 0.361 (95% CI 0.188 to 0.524) |
| Chance | 100.0% (38/38; 95% CI 90.8%–100.0%) | 40.2% (94/234; 95% CI 34.1%–46.6%) | 0.000 (95% CI -0.046 to 0.092) |

## Targets (Q25)

Measured on the final holdout run; dev values are shown for tracking. Targets are ambitions: the final results page states which were met.

| Metric | Baseline (v1) | Target | Current (v2) | Met on dev? |
|---|---|---|---|---|
| Youden's J | 0.435 | >= 0.600 | 0.327 | no |
| Clean flag rate | 41.5% | <= 20.0% | 56.1% | no |
| Precision | 68.5% | >= 80.0% | 66.9% | no |
| Strict category-correct recall | 51.2% | >= 60.0% | 51.2% | no |
| Cost per PR vs baseline | 1.00× | <= 3.00× | 1.15× | yes |
| p95 latency | 4.8 s | <= 30.0 s | 5.2 s | yes |

## Location matching: a diagnostic, not a headline

**Location recall at ±3 lines is non-discriminating on this benchmark:** on average 81.2% of a buggy case's changed lines lie inside its bug-holding ranges ±3 (median 100%; 46 of 80 cases at 100%). A reviewer that points anywhere in the diff lands on a labelled range, so the chance baseline scores higher than the reviewer.

| Strict location recall | Reviewer | Chance baseline |
|---|---|---|
| ±0 lines | 81.2% (65/80; 95% CI 71.3%–88.3%) | 75.0% (60/80; 95% CI 64.5%–83.2%) |
| ±1 lines | 81.2% (65/80; 95% CI 71.3%–88.3%) | 75.0% (60/80; 95% CI 64.5%–83.2%) |
| ±3 lines | 83.8% (67/80; 95% CI 74.2%–90.3%) | 95.0% (76/80; 95% CI 87.8%–98.0%) |

| Tier | Mode | Reviewer | Chance baseline |
|---|---|---|---|
| Lenient (any auto-labelled range) | location-only ⚠ | 88.8% (71/80; 95% CI 80.0%–94.0%) | 100.0% (80/80; 95% CI 95.4%–100.0%) |
| Lenient (any auto-labelled range) | category-correct | 55.0% (44/80; 95% CI 44.1%–65.4%) | 42.5% (34/80; 95% CI 32.3%–53.4%) |
| Strict (bug-holding ranges) | location-only ⚠ | 83.8% (67/80; 95% CI 74.2%–90.3%) | 95.0% (76/80; 95% CI 87.8%–98.0%) |
| Strict (bug-holding ranges) | category-correct | 51.2% (41/80; 95% CI 40.5%–61.9%) | 42.5% (34/80; 95% CI 32.3%–53.4%) |
| Primary-only | location-only ⚠ | 80.0% (64/80; 95% CI 70.0%–87.3%) | 88.8% (71/80; 95% CI 80.0%–94.0%) |
| Primary-only | category-correct | 51.2% (41/80; 95% CI 40.5%–61.9%) | 40.0% (32/80; 95% CI 30.0%–51.0%) |

⚠ location-only rows are non-discriminating at ±3 (base rate above).

## Micro and macro recall (strict, category-correct)

- Micro: 51.2% (41/80; 95% CI 40.5%–61.9%)
- Macro over categories with ≥5 kept cases: 0.535 (a mean of per-category rates; counts below)

| Category | Cases | Strict category-correct | Chance | Macro |
|---|---|---|---|---|
| type-or-contract | 34 | 58.8% (20/34; 95% CI 42.2%–73.6%) | 100.0% (34/34; 95% CI 89.8%–100.0%) | yes |
| control-flow | 17 | 64.7% (11/17; 95% CI 41.3%–82.7%) | 0.0% (0/17; 95% CI 0.0%–18.4%) | yes |
| concurrency-or-async | 9 | 33.3% (3/9; 95% CI 12.1%–64.6%) | 0.0% (0/9; 95% CI 0.0%–29.9%) | yes |
| error-handling | 7 | 57.1% (4/7; 95% CI 25.0%–84.2%) | 0.0% (0/7; 95% CI 0.0%–35.4%) | yes |
| null-or-none-handling | 4 | 50.0% (2/4; 95% CI 15.0%–85.0%) | 0.0% (0/4; 95% CI 0.0%–49.0%) | no (below floor) |
| off-by-one-or-boundary | 3 | 0.0% (0/3; 95% CI 0.0%–56.2%) | 0.0% (0/3; 95% CI 0.0%–56.2%) | no (below floor) |
| arithmetic-or-numeric | 2 | 0.0% (0/2; 95% CI 0.0%–65.8%) | 0.0% (0/2; 95% CI 0.0%–65.8%) | no (below floor) |
| resource-leak | 2 | 50.0% (1/2; 95% CI 9.5%–90.5%) | 0.0% (0/2; 95% CI 0.0%–65.8%) | no (below floor) |
| CWE-20 | 1 | 0.0% (0/1; 95% CI 0.0%–79.3%) | 0.0% (0/1; 95% CI 0.0%–79.3%) | no (below floor) |
| CWE-400 | 1 | 0.0% (0/1; 95% CI 0.0%–79.3%) | 0.0% (0/1; 95% CI 0.0%–79.3%) | no (below floor) |

## Clean cases

Every rate here carries the clean-case noise floor: 3 of 41 dev clean cases (7.3%) are marked suspicious, so up to that share of the clean flag rate may be label noise.

- Clean flag rate: 56.1% (23/41; 95% CI 41.0%–70.1%); mean findings per clean case 0.68. Chance baseline: 100.0% (41/41; 95% CI 91.4%–100.0%).

| Group | Clean cases with ≥1 finding | Mean findings |
|---|---|---|
| size 1-5 | 47.1% (8/17; 95% CI 26.2%–69.0%) | 0.59 |
| size 16-30 | 50.0% (4/8; 95% CI 21.5%–78.5%) | 0.62 |
| size 31-60 | 66.7% (2/3; 95% CI 20.8%–93.9%) | 0.67 |
| size 6-15 | 69.2% (9/13; 95% CI 42.4%–87.3%) | 0.85 |
| repo Textualize/rich | 50.0% (5/10; 95% CI 23.7%–76.3%) | 0.50 |
| repo agronholm/anyio | 75.0% (6/8; 95% CI 40.9%–92.9%) | 1.00 |
| repo fastapi/fastapi | 54.5% (6/11; 95% CI 28.0%–78.7%) | 0.73 |
| repo marshmallow-code/marshmallow | 50.0% (1/2; 95% CI 9.5%–90.5%) | 0.50 |
| repo pallets/click | 50.0% (5/10; 95% CI 23.7%–76.3%) | 0.60 |

**False-positive pattern** (28 findings on 23 clean cases): by category {'type-or-contract': 14, 'control-flow': 7, 'null-or-none-handling': 2, 'arithmetic-or-numeric': 1, 'concurrency-or-async': 1, 'off-by-one-or-boundary': 1, 'CWE-20': 1, 'error-handling': 1}; by severity {'medium': 15, 'high': 11, 'low': 2}; flagged by size {'1-5': '8/17', '16-30': '4/8', '31-60': '2/3', '6-15': '9/13'}; by repo {'Textualize/rich': '5/10', 'agronholm/anyio': '6/8', 'fastapi/fastapi': '6/11', 'marshmallow-code/marshmallow': '1/2', 'pallets/click': '5/10'}. Suspicious clean cases flagged: `1368e5b14e17732e`, `3350b7f5558de194`, `3fe0fe03cd5c9e75` (possibly true positives; see the label report).

## Recall by repo and by size (strict, category-correct)

| Group | Recall |
|---|---|
| repo Textualize/rich | 57.1% (4/7; 95% CI 25.0%–84.2%) |
| repo agronholm/anyio | 36.0% (9/25; 95% CI 20.2%–55.5%) |
| repo fastapi/fastapi | 60.9% (14/23; 95% CI 40.8%–77.8%) |
| repo marshmallow-code/marshmallow | 50.0% (4/8; 95% CI 21.5%–78.5%) |
| repo pallets/click | 58.8% (10/17; 95% CI 36.0%–78.4%) |
| size 1-5 lines | 63.3% (19/30; 95% CI 45.5%–78.1%) |
| size 16-30 lines | 31.2% (5/16; 95% CI 14.2%–55.6%) |
| size 31-60 lines | 40.0% (4/10; 95% CI 16.8%–68.7%) |
| size 6-15 lines | 54.2% (13/24; 95% CI 35.1%–72.1%) |

## Diagnostics

**Strict-location misses: 13.**

- findings on changed lines, outside the ±3 window: 3 (`08e903fe777a642c`, `2109faa46125df3d`, `4cf91dda2d9a58e3`)
- findings on context lines, outside the ±3 window: 1 (`5dd6a5f8d949c1df`)
- no findings: 9 (`24517970965f73df`, `26ad079673af9382`, `36b1a3b76394efc3`, `400cff6a304c125b`, `4ffca0ce378367c6`, `514024d672807316`, `8d2bb2c2fcb58432`, `94ad4f8fb317b04e`, `c3ee72768a1488f2`)

**Line coordinates** (124 findings): {'new-side, on an added line': 100, 'ambiguous: new-side context or old-side removed line': 13, 'new-side, context line': 11}. Most findings use new-file lines, as the labels do. A few cite removed lines by their old-file numbers, a convention the prompt does not set (Q65).

**Leak split** (cases whose removed lines matched the leak scan vs the rest):

- leak-scan matches (9): detection 100.0% (9/9; 95% CI 70.1%–100.0%); strict category-correct 44.4% (4/9; 95% CI 18.9%–73.3%)
- others (71): detection 87.3% (62/71; 95% CI 77.6%–93.2%); strict category-correct 52.1% (37/71; 95% CI 40.7%–63.3%)

## Security

Raw counts only; **not statistically meaningful** (too few cases, Q58): CWE-20 0/1, CWE-400 0/1.

## Operations

- Cases answered: 121/121; status: {'success': 121}
- Failures by type: none
- Parse-error rate: 0.0% (0/121; 95% CI 0.0%–3.1%)
- Cost: mean 0.00065 USD per case, total 0.0791 USD (LiteLLM list-price estimate; actual free-tier spend is $0)
- Latency: mean 2691 ms, p95 5220 ms (original call latency, also for cached cases)
- Tokens: prompt 157549, completion 98592
- Cache: 0.0% (0/121; 95% CI 0.0%–3.1%) cases served from cache; provider attempts 125
- Provider/model of answered cases: {'groq/openai/gpt-oss-120b': 121}; pinned-model share 100.0% (121/121; 95% CI 96.9%–100.0%); identical model ID across sessions: True

## Caveats

- **Location matching is non-discriminating on this benchmark:** on average 81.2% of a buggy case's changed lines lie inside its bug-holding ranges ±3 (median 100%; 46 of 80 cases at 100%). Location recall at ±3 is reported as a diagnostic only ([[ADR-025 Detection-first metrics]]).
- **Labels:** LLM-assigned from human-written upstream evidence. The owner verified them on a 28-case sample (25 stratified + 3 borderline): 25/25 agreement per field (95% lower bound 86.7%) ([[label-report-dev-2026-10-03]], [[Benchmark]]).
- **Clean-case noise floor: 3 of 41 dev clean cases (7.3%) are marked suspicious, so up to that share of the clean flag rate may be label noise.** Two of the three suspicious cases were flagged; one (click `3fe0fe03`) demonstrably introduced later bugs, and SZZ missed it because the code moved ([[Benchmark Leakage]]).
- **Category concentration:** `type-or-contract` is 34 of 80 kept cases (43%), which is also the chance baseline's category-correct recall. Macro recall covers only four categories, with the counts shown beside it.
- **Security is not measurable** here: 2 kept security cases.
- **Leakage profile:** 92% of buggy cases are after mid-2025; `Textualize/rich` has the weakest date profile ([[Benchmark Leakage]]). Issue references in removed lines are masked (`mask-issue-refs-v1`).
- **Single run:** run-to-run variance is not measured yet (Q63). The masked cases are fresh samples, so part of any change on them is that variance.
- **Diff-only review:** every eval case gets a neutral PR title to prevent label leakage; production passes the real title, so production performance may differ ([[Eval Harness]]).
- **Line-coordinate convention (Q65):** findings about removed code sometimes cite old-file line numbers; labels use new-file lines.
