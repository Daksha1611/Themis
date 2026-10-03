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

**Clean-case noise:** 3 of the 41 dev clean cases (7.3%) are marked suspicious. One of them is demonstrably a bug-introducing commit that SZZ missed because the buggy code moved ([[Benchmark Leakage]]). Every false-positive rate carries this noise floor ([[Metrics]]).

**Owner verification (2026-10-03):** the owner agreed with all 25 labels in a stratified sample, on every field (95% Wilson lower bound 86.7% per field). The 20 non-borderline drops were not sampled ([[Benchmark]]).

**Affects:** [[Benchmark]], [[Metrics]]
