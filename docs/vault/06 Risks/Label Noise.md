---
name: Label Noise
description: "Risk that some mined bug-fix labels are wrong, distorting the metrics."
type: risk
status: planned
tags: [risk]
related:
  - "[[Benchmark]]"
  - "[[Metrics]]"
---

# Label Noise

**Risk:** Some bug-fix commits are refactors, so some [[Benchmark]] labels will be wrong and distort [[Metrics]].

**Mitigation**
- Hand-check a sample
- Report the estimated noise rate

**Measured (M3):** the human labelling pass (`evals/benchmark/label.py`) records a drop reason for every dev case that is not a genuine bug fix; label noise = dropped / labelled dev cases, reported with the count ([[Benchmark]]). Single annotator.

**Affects:** [[Benchmark]], [[Metrics]]
