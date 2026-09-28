---
type: component
status: planned
tags: [component]
related:
  - "[[Review Graph]]"
  - "[[Finding Schema]]"
  - "[[Job Queue]]"
  - "[[HuggingFace Transformers]]"
  - "[[ADR-008 Encoder classifier as precision filter]]"
  - "[[Ablation Table]]"
  - "[[ADR-011 Finding outcomes as precision-filter labels]]"
  - "[[Storage]]"
---

# Precision Filter

**Purpose:** drop likely-noise findings before they are posted. Serves the headline metric, comment precision.

**Responsibilities**
- Score each finding with a small fine-tuned encoder classifier
- Drop findings that are likely noise
- Train on offline labels (cold start) and on the outcomes of posted findings, resolved or dismissed on the PR ([[ADR-011 Finding outcomes as precision-filter labels]])

**Inputs:** findings ([[Finding Schema]]) from the [[Review Graph]].
**Outputs:** the filtered findings to be posted.

**Planned code location:** `app/filter/` (inference); `training/label_findings.py`, `training/train_filter.py` (training).

**Dependencies:** [[HuggingFace Transformers]], [[Finding Schema]]. Decisions: [[ADR-008 Encoder classifier as precision filter]], [[ADR-011 Finding outcomes as precision-filter labels]]. Finding outcomes are read from [[Storage]]. Measured as its own row in the [[Ablation Table]]. Score threshold is not yet specified.
