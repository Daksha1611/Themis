---
name: ADR-008 Encoder classifier as precision filter
description: "Decision: a small fine-tuned encoder classifier is the precision filter."
type: decision
status: superseded
tags: [decision]
related:
  - "[[Precision Filter]]"
  - "[[transformers]]"
  - "[[Metrics]]"
  - "[[Ablation Table]]"
  - "[[ADR-031 Consistency-based precision filter]]"
---

# ADR-008 Encoder classifier as precision filter

> **Superseded by [[ADR-031 Consistency-based precision filter]] (2026-10-29).** Measured on the dev findings, neither CodeBERT (frozen or fine-tuned) nor a feature-based classifier could separate real findings from noise ([[precision-filter-dev-2026-10-29]]).

## Context
Comment precision is the headline metric; noisy findings erode trust.

## Decision
A small fine-tuned encoder classifier ([[transformers]]) scores each finding and drops likely noise before posting ([[Precision Filter]]).

## Alternatives considered
- None stated in the spec.

## Consequences
- Requires a training pipeline in `training/` (`label_findings.py`, `train_filter.py`).
- Measured as the "+ precision filter" row of the [[Ablation Table]].
