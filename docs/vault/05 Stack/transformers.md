---
name: transformers
description: "HuggingFace Transformers: the CodeBERT encoder for the precision filter."
type: tech
status: in-progress
tags: [tech]
related:
  - "[[Precision Filter]]"
  - "[[ADR-008 Encoder classifier as precision filter]]"
  - "[[ADR-030 v1 finish plan and scope cuts]]"
version: 5.18.0 (pinned in the filter extra; read via uv pip show 2026-10-29)
---

# transformers (HuggingFace)

**What it is:** Python library for pretrained transformer models.

**What it does in Themis:** Loads `microsoft/codebert-base` on CPU for the precision filter's encoder variant: embeddings of each finding, and optionally fine-tuning (`training/train_filter.py`). The candidate `deberta-v3-small` is not tried in v1.

**Used by:** [[Precision Filter]], [[ADR-008 Encoder classifier as precision filter]]

**Version:** 5.18.0, also a dependency of [[sentence-transformers]].
