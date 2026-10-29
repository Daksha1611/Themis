---
name: scikit-learn
description: "scikit-learn: the precision filter's feature-based reference model, grouped cross-validation and the precision-recall sweep."
type: tech
status: in-progress
tags: [tech]
related:
  - "[[Precision Filter]]"
  - "[[ADR-030 v1 finish plan and scope cuts]]"
version: 1.9.1 (pinned in the filter extra; read via uv pip show 2026-10-29)
---

# scikit-learn

**What it is:** Python machine-learning library.

**What it does in Themis:** The precision filter's reference classifier over finding features, the linear head on encoder embeddings, `GroupKFold` cross-validation by case ID, and precision-recall curves for the threshold sweep (`training/train_filter.py`).

**Used by:** [[Precision Filter]]

**Version:** 1.9.1, also a dependency of [[sentence-transformers]].
