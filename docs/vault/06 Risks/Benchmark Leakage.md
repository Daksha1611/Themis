---
name: Benchmark Leakage
description: "Risk that the model memorised benchmark fixes or holdout leaks into tuning; measured commit-date distribution."
type: risk
status: in-progress
tags: [risk]
related:
  - "[[Benchmark]]"
  - "[[Eval Harness]]"
  - "[[Precision Filter]]"
  - "[[Ablation Table]]"
  - "[[ADR-017 Dev-split-only training data for the precision filter]]"
  - "[[ADR-007 dev-holdout benchmark split]]"
---

# Benchmark Leakage

**Risk:** the single biggest threat to the project's headline claim. If the model had already seen these fixes, every number is worthless.

Two forms:
- **Model memorisation:** the LLM saw the bug-fix commits in training.
- **Holdout contamination:** holdout cases leak into tuning or into precision-filter training.

**Mitigation**
- Prefer commits after mid-2025 within the 2025-04-01 → 2026-10-01 window, and record each case's commit date so results can be split by it ([[Benchmark]]). In place: the date distribution below. Planned: the dates on every case (M3 Step 3)
- Prefer mid-popularity repos over famous ones ([[Benchmark]])
- Run holdout only at milestones ([[ADR-007 dev-holdout benchmark split]]). Planned: the M3 runner refuses the holdout split without an explicit flag
- Train the precision filter on dev-split findings only, enforced in code ([[ADR-017 Dev-split-only training data for the precision filter]]). Planned (M5)

## Measured date distribution (M3 Step 1, 2026-10-01)
Package-scoped bug-fix commits in the candidate window (2025-04-01 → 2026-10-01), by quarter:

| Repo | 2025-Q2 | 2025-Q3 | 2025-Q4 | 2026-Q1 | 2026-Q2 | 2026-Q3 | After 2025-07-01 |
|---|---|---|---|---|---|---|---|
| pallets/click | 6 | 12 | 3 | 1 | 33 | 10 | 59 / 65 (90%) |
| marshmallow-code/marshmallow | 2 | 2 | 5 | 11 | 3 | 3 | 24 / 26 (92%) |
| Textualize/rich | 8 | 1 | 2 | 10 | 3 | 0 | 16 / 24 (66%) |
| agronholm/anyio | 5 | 5 | 5 | 9 | 15 | 28 | 62 / 67 (92%) |
| fastapi/fastapi | 3 | 6 | 27 | 8 | 3 | 11 | 55 / 58 (94%) |

Most candidates sit after mid-2025. `Textualize/rich` has the largest share before it (34%). `fastapi/fastapi` is very famous (higher memorisation risk), offset by 94% of its fixes being recent. Whether a given fix predates a specific model's training cutoff still depends on the model; the date is recorded per case so results can be split by it.

**The window start is what reduced the viable set.** Starting at 2025-04-01 (to limit leakage) leaves only three repos with ≥40 package-scoped bug-fix commits (`pallets/click`, `agronholm/anyio`, `fastapi/fastapi`), so there is little room to tighten the window further. The benchmark uses five repos (Q20), adding `marshmallow-code/marshmallow` and `Textualize/rich` below that bar.

## Mined-commit date distribution (M3 Step 3, 2026-10-02)
Buggy cases actually built, by quarter of the fix commit:

| Repo | 2025-Q2 | 2025-Q3 | 2025-Q4 | 2026-Q1 | 2026-Q2 | 2026-Q3 | After 2025-07-01 |
|---|---|---|---|---|---|---|---|
| pallets/click | 4 | 7 | 2 | 1 | 23 | 5 | 38/42 |
| agronholm/anyio | 3 | 2 | 4 | 8 | 11 | 26 | 51/54 |
| fastapi/fastapi | 2 | 4 | 20 | 5 | 2 | 7 | 38/40 |
| marshmallow-code/marshmallow | 1 | 0 | 3 | 9 | 2 | 1 | 15/16 |
| Textualize/rich ⚠ weakest date profile | 4 | 0 | 2 | 9 | 1 | 0 | 12/16 |

`Textualize/rich` remains the weakest (12/16 after mid-2025, none after 2026-Q2). Overall 154 of 168 buggy cases (92%) are after mid-2025.

## Required M3 output
M3 Step 1 output must include **the date distribution of the actually-mined commits, bucketed by quarter, per repo**, not only of the candidate pool above. A window starting 2025-04-01 sits before several current models' training cutoffs. **`Textualize/rich` has the weakest date profile** (its candidates end in 2026-04, and only 66% are after mid-2025); every per-repo date report names it explicitly.

**Rule:** if a substantial fraction of mined commits predates mid-2025, that caveat goes **on the public results page itself**, where a reader will see it, not only in this note ([[Ablation Table]], `evals/report.py`).

**Affects:** [[Benchmark]], [[Eval Harness]], [[Precision Filter]]
