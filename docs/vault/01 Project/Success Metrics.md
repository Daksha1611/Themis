---
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

## Shape of success
Numeric targets are deferred until baseline numbers exist. Success means:
- Precision improves meaningfully over the baseline
- Recall does not fall more than a small margin
- Cost per PR stays under a stated ceiling

Real numbers are filled in after the baseline eval run ([[Open Questions]], Q25).
