---
name: ADR-008 Encoder classifier as precision filter
description: "Decision: a small fine-tuned encoder classifier is the precision filter."
type: decision
status: accepted
tags: [decision]
related:
  - "[[Precision Filter]]"
  - "[[HuggingFace Transformers]]"
  - "[[Metrics]]"
  - "[[Ablation Table]]"
---

# ADR-008 Encoder classifier as precision filter

## Context
Comment precision is the headline metric; noisy findings erode trust.

## Decision
A small fine-tuned encoder classifier ([[HuggingFace Transformers]]) scores each finding and drops likely noise before posting ([[Precision Filter]]).

## Alternatives considered
- None stated in the spec.

## Consequences
- Requires a training pipeline in `training/` (`label_findings.py`, `train_filter.py`).
- Measured as the "+ precision filter" row of the [[Ablation Table]].
