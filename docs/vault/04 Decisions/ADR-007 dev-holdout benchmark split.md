---
name: ADR-007 dev-holdout benchmark split
description: "Decision: a dev split for tuning and a holdout split run only at milestones."
type: decision
status: accepted
tags: [decision]
related:
  - "[[Benchmark]]"
  - "[[Eval Harness]]"
  - "[[CI Quality Gate]]"
  - "[[Eval Cost]]"
  - "[[ADR-017 Dev-split-only training data for the precision filter]]"
---

# ADR-007 dev-holdout benchmark split

## Context
Tuning against the same cases used to report results would overstate quality. Eval runs cost money ([[Eval Cost]]).

## Decision
The [[Benchmark]] has two splits: **dev** (for tuning) and **holdout** (run only at milestones).

## Alternatives considered
- None stated in the spec.

## Consequences
- The [[CI Quality Gate]] runs only the dev split.
- Holdout is run only at milestones / completion.
- Split ratio: 60% dev / 40% holdout, stratified by repo and bug category (see [[Benchmark]]).
- The precision filter trains on dev-split findings only ([[ADR-017 Dev-split-only training data for the precision filter]]).
