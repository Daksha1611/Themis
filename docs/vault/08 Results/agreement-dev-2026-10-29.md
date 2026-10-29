---
name: agreement-dev-2026-10-29
description: "Agreement of findings across cached dev runs (v1, v1 rerun, v2) and the voting rule flag-if-m-of-k-agree, with bootstrap CIs (ADR-031 Step 1)."
type: reliability
status: done
tags: [reliability, results]
related:
  - "[[ADR-031 Consistency-based precision filter]]"
  - "[[Precision Filter]]"
  - "[[precision-filter-dev-2026-10-29]]"
  - "[[ADR-029 Aggregated evaluation]]"
---

# Agreement across runs, dev split (2026-10-29)

From the cached runs; **no LLM calls**, holdout untouched. Matching: same file, line ranges within ±3, and the same category (**strict**) or any category (**location**). Clusters are connected components of matching findings; a finding's agreement count is the number of runs in its cluster. Real or noise as in [[precision-filter-dev-2026-10-29]] (within ±3 of a strict bug-holding range of a buggy case). Voting keeps one finding per cluster with at least m runs. CIs: stratified percentile bootstrap over cases (2000 resamples). The single-run reference is the mean of the k runs.

## (a) v1, v1 rerun and v2 (k = 3)

**Agreement count of each finding** (findings, all runs):

| Mode | Kind | 1 of 3 | 2 of 3 | 3 of 3 | Share at ≥ 2 |
|---|---|---|---|---|---|
| strict | real | 46 | 46 | 139 | 80.1% |
| strict | noise | 54 | 31 | 33 | 54.2% |
| location | real | 14 | 23 | 194 | 93.9% |
| location | noise | 30 | 40 | 48 | 74.6% |

**Voting rules:**

| Rule | J | Detection | Clean flag rate | Precision | Category-correct | Findings |
|---|---|---|---|---|---|---|
| single run (mean of k) | 0.383 (0.232 to 0.525) | 87.9% (81.2% to 93.8%) | 49.6% (37.4% to 62.6%) | 66.2% (59.8% to 72.4%) | 49.2% (40.4% to 58.3%) | 116 |
| strict, >= 1 of 3 | 0.279 (0.121 to 0.427) | 93.8% (87.5% to 98.8%) | 65.9% (51.2% to 80.5%) | 59.7% (52.5% to 67.5%) | 62.5% (52.5% to 73.8%) | 191 |
| strict, >= 2 of 3 | 0.422 (0.240 to 0.594) | 81.2% (72.5% to 88.8%) | 39.0% (24.4% to 53.7%) | 74.7% (67.0% to 82.4%) | 52.5% (41.2% to 63.7%) | 91 |
| strict, >= 3 of 3 | 0.379 (0.209 to 0.540) | 55.0% (43.8% to 66.2%) | 17.1% (7.3% to 29.3%) | 83.6% (74.1% to 92.7%) | 33.8% (23.8% to 45.0%) | 55 |
| location, >= 1 of 3 | 0.279 (0.121 to 0.427) | 93.8% (87.5% to 98.8%) | 65.9% (51.2% to 80.5%) | 57.1% (50.3% to 64.3%) | 57.5% (46.2% to 68.8%) | 147 |
| location, >= 2 of 3 | 0.338 (0.165 to 0.498) | 85.0% (76.2% to 92.5%) | 51.2% (36.6% to 65.9%) | 68.0% (60.5% to 75.0%) | 52.5% (41.2% to 62.5%) | 103 |
| location, >= 3 of 3 | 0.481 (0.309 to 0.642) | 72.5% (62.5% to 82.5%) | 24.4% (12.2% to 39.0%) | 81.1% (72.7% to 89.7%) | 46.2% (35.0% to 57.5%) | 74 |
| chance baseline | 0.000 (0.000 to 0.000) | 100.0% (100.0% to 100.0%) | 100.0% (100.0% to 100.0%) | 38.7% (33.9% to 44.4%) | 42.5% (31.2% to 52.5%) | 243 |

**Paired against the single-run reference** (net cases, bootstrap 95% CI, permutation p; negative = fewer):

| Rule | Detection (of 80) | Clean flags (of 41) | Category-correct (of 80) |
|---|---|---|---|
| strict, >= 1 of 3 | +4.67 (+2.0 to +7.7), p = 0.001 | +6.67 (+3.7 to +10.0), p = 0.000 | +10.67 (+6.7 to +14.7), p = 0.000 |
| strict, >= 2 of 3 | -5.33 (-10.0 to -1.3), p = 0.021 | -4.33 (-8.3 to -0.3), p = 0.058 | +2.67 (-0.7 to +6.0), p = 0.166 |
| strict, >= 3 of 3 | -26.33 (-34.3 to -18.7), p = 0.000 | -13.33 (-18.3 to -8.7), p = 0.000 | -12.33 (-17.3 to -7.7), p = 0.000 |
| location, >= 1 of 3 | +4.67 (+2.0 to +7.7), p = 0.001 | +6.67 (+3.7 to +10.0), p = 0.000 | +6.67 (+2.7 to +10.7), p = 0.003 |
| location, >= 2 of 3 | -2.33 (-6.0 to +0.7), p = 0.240 | +0.67 (-1.7 to +3.0), p = 0.794 | +2.67 (-1.0 to +6.3), p = 0.215 |
| location, >= 3 of 3 | -12.33 (-18.0 to -7.0), p = 0.000 | -10.33 (-14.7 to -6.3), p = 0.000 | -2.33 (-6.7 to +1.7), p = 0.355 |

**Rules within 5 points of single-run detection:** strict, >= 1 of 3 (detection +5.8 points, clean flag rate +16.3 points); location, >= 1 of 3 (detection +5.8 points, clean flag rate +16.3 points); location, >= 2 of 3 (detection -2.9 points, clean flag rate +1.6 points)

## (b) v1 and v1 rerun only (k = 2, identical configuration)

**Agreement count of each finding** (findings, all runs):

| Mode | Kind | 1 of 2 | 2 of 2 | Share at ≥ 2 |
|---|---|---|---|---|
| strict | real | 44 | 104 | 70.3% |
| strict | noise | 46 | 31 | 40.3% |
| location | real | 15 | 133 | 89.9% |
| location | noise | 31 | 46 | 59.7% |

**Voting rules:**

| Rule | J | Detection | Clean flag rate | Precision | Category-correct | Findings |
|---|---|---|---|---|---|---|
| single run (mean of k) | 0.412 (0.259 to 0.559) | 87.5% (80.0% to 93.8%) | 46.3% (34.1% to 59.8%) | 65.8% (58.4% to 72.9%) | 48.1% (38.8% to 57.5%) | 112 |
| strict, >= 1 of 2 | 0.303 (0.131 to 0.462) | 91.2% (83.8% to 96.2%) | 61.0% (46.3% to 75.6%) | 62.6% (54.5% to 70.7%) | 60.0% (50.0% to 71.2%) | 155 |
| strict, >= 2 of 2 | 0.418 (0.245 to 0.589) | 63.7% (52.5% to 73.8%) | 22.0% (9.8% to 34.1%) | 81.5% (73.0% to 90.0%) | 40.0% (28.7% to 51.2%) | 65 |
| location, >= 1 of 2 | 0.303 (0.131 to 0.462) | 91.2% (83.8% to 96.2%) | 61.0% (46.3% to 75.6%) | 61.5% (54.2% to 68.9%) | 55.0% (43.8% to 66.2%) | 130 |
| location, >= 2 of 2 | 0.495 (0.323 to 0.655) | 78.8% (68.8% to 87.5%) | 29.3% (17.1% to 43.9%) | 77.4% (68.7% to 85.9%) | 48.8% (37.5% to 60.0%) | 84 |
| chance baseline | 0.000 (0.000 to 0.000) | 100.0% (100.0% to 100.0%) | 100.0% (100.0% to 100.0%) | 38.7% (33.9% to 44.4%) | 42.5% (31.2% to 52.5%) | 243 |

**Paired against the single-run reference** (net cases, bootstrap 95% CI, permutation p; negative = fewer):

| Rule | Detection (of 80) | Clean flags (of 41) | Category-correct (of 80) |
|---|---|---|---|
| strict, >= 1 of 2 | +3.00 (+1.0 to +5.5), p = 0.034 | +6.00 (+3.5 to +9.0), p = 0.001 | +9.50 (+6.0 to +13.5), p = 0.000 |
| strict, >= 2 of 2 | -19.00 (-26.5 to -12.0), p = 0.000 | -10.00 (-14.0 to -6.0), p = 0.000 | -6.50 (-10.5 to -2.5), p = 0.005 |
| location, >= 1 of 2 | +3.00 (+1.0 to +5.5), p = 0.034 | +6.00 (+3.5 to +9.0), p = 0.001 | +5.50 (+1.5 to +9.5), p = 0.020 |
| location, >= 2 of 2 | -7.00 (-11.5 to -3.0), p = 0.001 | -7.00 (-10.5 to -4.0), p = 0.000 | +0.50 (-4.0 to +5.0), p = 1.000 |

**Rules within 5 points of single-run detection:** strict, >= 1 of 2 (detection +3.7 points, clean flag rate +14.6 points); location, >= 1 of 2 (detection +3.7 points, clean flag rate +14.6 points)
## Gate for building the filter (ADR-031 Step 2)

Build only if a rule cuts the clean flag rate materially (paired 95% CI on clean-flag net cases entirely below 0) while detection stays within 5 points of the single-run reference.

- **(a):** no rule passes.
- **(b):** no rule passes.
