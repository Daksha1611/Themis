---
name: ADR-025 Detection-first metrics
description: "Decision: headline metrics are Youden's J, category-correct recall, precision and clean flag rate; location recall at ±3 is a diagnostic; ablations use paired McNemar tests."
type: decision
status: accepted
tags: [decision]
related:
  - "[[Metrics]]"
  - "[[Benchmark]]"
  - "[[Eval Harness]]"
  - "[[baseline-dev-2026-10-04]]"
---

# ADR-025 Detection-first metrics

Owner decision, 2026-10-04. Refines the headline in [[Metrics]].

## Context
The first dev baseline ([[baseline-dev-2026-10-03]]) used strict location recall at ±3 lines. A chance baseline that flags the first changed line of every hunk scored **95% strict location recall** (lenient 100%), against the reviewer's 80%.

The cause is structural. Benchmark diffs are small, and their labels are the changed lines: **on average 81.2% of a buggy case's changed lines lie inside its bug-holding ranges ±3** (median 100%; 46 of 80 kept cases at 100%). On this benchmark, location matching cannot separate a reviewer from chance.

## Decision
**Headline metrics,** each computed for the reviewer and the chance baseline side by side, with k/n and a 95% interval:
- **Youden's J** = detection rate (TPR: buggy cases with ≥1 finding) − clean flag rate (FPR: clean cases with ≥1 finding). The interval uses Newcombe's hybrid score method for a difference of two independent proportions. A reviewer that flags at random, including the chance baseline, scores 0.
- **Strict category-correct recall.** The chance baseline's value equals the majority-class rate (`type-or-contract`, 34 of 80).
- **Precision:** findings landing on a bug-holding range, over all findings.
- **Clean flag rate,** with the clean-case noise floor (3 of 41 suspicious).

**Location recall** at ±3 stays in reports, labelled non-discriminating on this benchmark with the base rate beside it. Strict location recall at ±0 and ±1 is reported as a secondary diagnostic.

**Comparisons between runs** (every future ablation) use an **exact McNemar test on paired cases**: detection, strict category-correct recall, and clean flags, each with the discordant counts (b, c) and the p-value. Overlapping confidence intervals are never used as the test.

## Consequences
- The headline measures whether the reviewer finds something on buggy diffs and stays quiet on clean ones, and whether it names the bug's kind. It does not reward pointing at lines that are, on this benchmark, nearly all labelled.
- **Location precision becomes meaningful again** if the benchmark gains larger diffs, where changed lines far outnumber the bug-holding ones. The base-rate diagnostic is reported every run, so that shift is visible.
