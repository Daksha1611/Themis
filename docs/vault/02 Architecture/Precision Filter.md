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
---

# Precision Filter

**Purpose:** drop likely-noise findings before they are posted. Serves the headline metric, comment precision.

**Responsibilities**
- Score each finding with a small fine-tuned encoder classifier
- Drop findings that are likely noise

**Inputs:** findings ([[Finding Schema]]) from the [[Review Graph]].
**Outputs:** the filtered findings to be posted.

**Planned code location:** `app/filter/` (inference); `training/label_findings.py`, `training/train_filter.py` (training).

**Dependencies:** [[HuggingFace Transformers]], [[Finding Schema]]. Decision: [[ADR-008 Encoder classifier as precision filter]]. Measured as its own row in the [[Ablation Table]]. Score threshold is not yet specified.
