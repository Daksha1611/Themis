---
type: decision
status: done
tags: [decision]
related:
  - "[[Benchmark]]"
  - "[[Eval Harness]]"
  - "[[CI Quality Gate]]"
  - "[[Eval Cost]]"
---

# ADR-007 dev-holdout benchmark split

**Status:** accepted

## Context
Tuning against the same cases used to report results would overstate quality. Eval runs cost money ([[Eval Cost]]).

## Decision
The [[Benchmark]] has two splits: **dev** (for tuning) and **holdout** (run only at milestones).

## Alternatives considered
- None stated in the spec.

## Consequences
- The [[CI Quality Gate]] runs only the dev split.
- Holdout is run only at milestones / completion.
