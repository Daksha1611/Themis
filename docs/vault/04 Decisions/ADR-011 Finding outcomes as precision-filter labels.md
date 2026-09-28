---
type: decision
status: done
tags: [decision]
related:
  - "[[Precision Filter]]"
  - "[[Storage]]"
  - "[[Benchmark]]"
  - "[[Non-Goals]]"
  - "[[Prior Art]]"
---


# ADR-011 Finding outcomes as precision-filter labels

**Status:** accepted

## Context
The [[Precision Filter]] needs labeled findings (useful vs noise). Offline labeling alone never improves from real use. Inspired by the Learner service in [[Prior Art]], but applied to precision, not style.

## Decision
When a posted finding is later resolved or dismissed on the PR, that outcome is recorded in [[Storage]] and used as a training label for the [[Precision Filter]]. Offline labeling (`training/label_findings.py`) remains for the cold start.

## Alternatives considered
- Offline labels only: no real-world signal.
- Learning style patterns from merged PRs (as in the prior art): style is a [[Non-Goals|non-goal]].

## Consequences
- [[Storage]] records finding outcomes.
- Labels exist only after Themis is deployed and posting comments.
- Outcome labels are noisy; the exact signal for "resolved" and "dismissed" must be defined (see [[Open Questions]]).
- Outcomes from [[Benchmark]] repos must not leak into the holdout split.
