---
type: risk
status: planned
tags: [risk]
related:
  - "[[Benchmark]]"
  - "[[Eval Harness]]"
  - "[[Precision Filter]]"
  - "[[ADR-017 Dev-split-only training data for the precision filter]]"
  - "[[ADR-007 dev-holdout benchmark split]]"
---

# Benchmark Leakage

**Risk:** the single biggest threat to the project's headline claim. If the model had already seen these fixes, every number is worthless.

Two forms:
- **Model memorisation:** the LLM saw the bug-fix commits in training.
- **Holdout contamination:** holdout cases leak into tuning or into precision-filter training.

**Mitigation**
- Pin the commit range to dates after the primary model's training cutoff ([[Benchmark]])
- Prefer mid-popularity repos over famous ones ([[Benchmark]])
- Run holdout only at milestones ([[ADR-007 dev-holdout benchmark split]])
- Train the precision filter on dev-split findings only, enforced in code ([[ADR-017 Dev-split-only training data for the precision filter]])

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

**Affects:** [[Benchmark]], [[Eval Harness]], [[Precision Filter]]
