---
name: Success Metrics
description: "How success is judged: comment precision is the headline metric; numeric targets wait for the baseline (Q25)."
type: project
status: done
tags: [project]
related:
  - "[[Metrics]]"
  - "[[CI Quality Gate]]"
  - "[[Ablation Table]]"
  - "[[Vision]]"
---

# Success Metrics

Themis succeeds when its review quality is measured and defended by numbers ([[Vision]]).

- **Comment precision** is the headline metric.
- Full metric definitions: [[Metrics]] (bug recall, comment precision, false-positive rate on clean PRs, cost per PR, p95 latency, injection resistance).
- Regressions are blocked by the [[CI Quality Gate]].
- The final deliverable showing each design decision's effect is the [[Ablation Table]].

## Targets (Q25, decided 2026-10-04)
Measured on the **final holdout run**. Baseline values are dev baseline v1 ([[baseline-dev-2026-10-04]]); definitions: [[Metrics]], [[ADR-025 Detection-first metrics]].

| Metric | Baseline (dev v1) | Target |
|---|---|---|
| Youden's J | 0.435 | ≥ 0.60 |
| Clean flag rate | 41.5% | ≤ 20% |
| Precision | 68.5% | ≥ 80% |
| Strict category-correct recall | 51.2% | ≥ 60% |
| Cost per PR (list-price estimate) | 0.00057 USD | ≤ 3× baseline |
| p95 latency | 4.8 s | ≤ 30 s |

**Rule:** each claimed improvement must be McNemar-significant against the previous ablation row on dev, **and** its disagreement count must exceed the measured run-to-run noise ([[Metrics]], Q63). Targets are ambitions: the final results page states which were met and which were not.
