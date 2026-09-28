---
type: decision
status: accepted
tags: [decision]
related:
  - "[[Precision Filter]]"
  - "[[Benchmark]]"
  - "[[Benchmark Leakage]]"
  - "[[ADR-007 dev-holdout benchmark split]]"
  - "[[ADR-011 Finding outcomes as precision-filter labels]]"
---

# ADR-017 Dev-split-only training data for the precision filter

## Context
The [[Precision Filter]] is trained on labeled findings from benchmark runs. Training on holdout findings would leak the holdout into the model and inflate every holdout number ([[Benchmark Leakage]]).

## Decision
**Hard rule:** the Precision Filter is trained only on findings generated from **dev-split** cases, never holdout.

- Enforced in code: `training/build_training_set.py` rejects any case ID present in the holdout split.
- Stated in the root `README.md`.

**Label sources**
1. Manual labeling of findings from dev-split runs
2. LLM-assisted pre-labeling with human verification
3. Later, real outcome signals ([[ADR-011 Finding outcomes as precision-filter labels]])

## Alternatives considered
- None stated.

## Consequences
- Training data is limited to the dev split.
- New file `training/build_training_set.py`.
