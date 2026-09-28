---
type: reliability
status: planned
tags: [reliability]
related:
  - "[[Eval Harness]]"
  - "[[Success Metrics]]"
  - "[[CI Quality Gate]]"
  - "[[Ablation Table]]"
  - "[[Guardrails]]"
---

# Metrics

| Metric | Definition |
|---|---|
| Bug recall | Seeded bugs flagged at the correct location |
| **Comment precision** | Headline metric |
| False-positive rate | On clean PRs |
| Cost per PR | |
| p95 latency | |
| Injection resistance | Measured against [[Guardrails]] with `evals/injection/` |

**Planned code location:** `evals/metrics.py`.

Used by the [[CI Quality Gate]], [[Drift Monitoring]], and the [[Ablation Table]]. See [[Success Metrics]].
