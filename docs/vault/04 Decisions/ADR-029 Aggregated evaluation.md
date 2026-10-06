---
name: ADR-029 Aggregated evaluation
description: "Decision: every configuration is evaluated with k = 3 runs, per-case outcomes are means over the runs, and comparisons use a paired permutation test with a bootstrap CI; single-run McNemar becomes directional only."
type: decision
status: accepted
tags: [decision]
related:
  - "[[Metrics]]"
  - "[[Eval Harness]]"
  - "[[ADR-024 Eval runs pin a single provider and model]]"
  - "[[ADR-025 Detection-first metrics]]"
  - "[[Free Tier Throughput]]"
---

# ADR-029 Aggregated evaluation

Owner decision, 2026-10-06. Supersedes the single-run McNemar rule in [[Metrics]], which is kept there as history.

## Context
- **Outputs cannot be made reproducible on this provider.** In the determinism probe, every call landed on a different backend build (`system_fingerprint`), even with a fixed seed. Groq documents its seed as best effort.
- **Identical runs disagree substantially.** v1 and its no-cache rerun disagreed on 19 of 80 category-correct outcomes, 12 of 41 clean flags and 6 of 80 detections.
- **Single-run comparisons are underpowered.** The minimum detectable effect of an exact McNemar test at 80% power is about 18 net cases for category-correct recall and 15 for clean flags ([[Metrics]]).
- **A per-case majority vote would not help:** the unstable cases are close to coin flips, so the majority of several runs is still a coin flip. Averaging reduces the variance; voting does not.

## Decision
- **k = 3 runs per configuration.** The per-case outcome (detection, strict category-correct, clean flag) is the **mean over the k runs**.
- **Comparisons** between configurations use a **paired permutation test on the per-case means** (two-sided, sign-flip), plus a **bootstrap 95% CI on the difference** (resampling cases). The effect is reported as **net cases fixed**, with the interval.
- **Single-run McNemar** results remain reportable, but only as directional.
- **Power at k = 3** (simulated from the per-case variance observed between v1 and its rerun; two-sided, α = 0.05, 80% power), in net cases fixed:

  | Measure | k = 1 (≈ McNemar) | k = 3 | k = 5 |
  |---|---|---|---|
  | Detection | 13 | 9 | 8 |
  | Strict category-correct | 17 | 11 | 9 |
  | Clean flags | 16 | 9 | 8 |

  Falsification subsets at k = 3: about 9 net cases each for category-correct and clean flags.

## Consequences
- **Cost:** each configuration costs three runs of Groq quota (a plain run ≈ 1.3 days; a run with context at 1K ≈ 2.1 days, at medium reasoning effort). An ablation row takes about a week.
- **Interpretation:** a smaller real effect becomes detectable (about 11 net category fixes instead of 18), though effects of a few cases stay below what this benchmark can show.
- **Reporting:** results pages state in plain words that individual runs are not reproducible.
