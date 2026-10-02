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

**Affects:** [[Benchmark]], [[Metrics]]
