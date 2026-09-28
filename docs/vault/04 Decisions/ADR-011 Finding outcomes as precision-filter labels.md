---
type: decision
status: accepted
tags: [decision]
related:
  - "[[Precision Filter]]"
  - "[[Storage]]"
  - "[[GitHub Integration]]"
  - "[[Benchmark]]"
  - "[[Non-Goals]]"
  - "[[Prior Art]]"
  - "[[ADR-017 Dev-split-only training data for the precision filter]]"
---

# ADR-011 Finding outcomes as precision-filter labels

## Context
Inspired by the Learner service in [[Prior Art]], applied to precision, not style. Installing Themis on the owner's own repos will produce dozens of findings, not the thousands a classifier needs.

## Decision
Outcome signals are a **demonstrated mechanism with a small pilot sample**, not a primary label source. Primary training labels come from [[ADR-017 Dev-split-only training data for the precision filter]].

**Signal definitions**
- **Validated:** code at or near the flagged line changes in a later commit on the same PR.
- **Dismissed:** the thread is resolved with no code change, or a maintainer reacts negatively.

Raw signals are stored separately from the derived label, so the rule can be revised later without losing data.

**This signal is noisy.** People resolve threads for many reasons.

## Alternatives considered
- Outcome labels as the primary label source: too few findings for a classifier.
- Learning style patterns from merged PRs (as in the prior art): style is a [[Non-Goals|non-goal]].

## Consequences
- [[GitHub Integration]] reads outcome signals (later commits, thread resolution, reactions).
- [[Storage]] keeps raw signals and derived labels separately.
- Results that use outcome labels state the pilot sample size.
- Outcomes from [[Benchmark]] repos must not leak into the holdout split.
