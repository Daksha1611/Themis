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

**Affects:** [[Benchmark]], [[Eval Harness]], [[Precision Filter]]
