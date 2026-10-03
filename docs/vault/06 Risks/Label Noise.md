---
name: Label Noise
description: "Risk that some mined bug-fix labels are wrong, distorting the metrics."
type: risk
status: in-progress
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

**Measured (M3, dev split, 2026-10-03):** every buggy dev case that is not a genuine bug fix gets a drop reason in the labelling pass. Results:
- **Upper bound: 22 of 102 buggy cases dropped (21.6%).** 9 of the drops are `o`, 8 of those `external-compat`.
- Excluding `o`: 13 of 102 (12.7%).

The labels were made by the development assistant from upstream evidence (Q61 amendment, [[Benchmark]]), with a single annotator. Report: [[label-report-dev-2026-10-03]].

**Affects:** [[Benchmark]], [[Metrics]]
