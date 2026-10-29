---
name: Precision Filter
description: "Encoder classifier that sets each finding's confidence and drops likely noise before posting."
type: component
status: in-progress
tags: [component]
related:
  - "[[Review Graph]]"
  - "[[Guardrails]]"
  - "[[Finding Schema]]"
  - "[[GitHub Integration]]"
  - "[[Storage]]"
  - "[[Eval Harness]]"
  - "[[transformers]]"
  - "[[ADR-008 Encoder classifier as precision filter]]"
  - "[[ADR-011 Finding outcomes as precision-filter labels]]"
  - "[[ADR-030 v1 finish plan and scope cuts]]"
  - "[[scikit-learn]]"
  - "[[precision-filter-dev-2026-10-29]]"
  - "[[ADR-016 Confidence comes from the precision filter, not the LLM]]"
  - "[[ADR-017 Dev-split-only training data for the precision filter]]"
  - "[[Benchmark Leakage]]"
  - "[[Ablation Table]]"
---

# Precision Filter

**Purpose:** drop likely-noise findings before they are posted. Serves the headline metric, comment precision.

**Responsibilities**
- Score each finding with a small fine-tuned encoder classifier; the score is the finding's `confidence` (0.0–1.0) ([[ADR-016 Confidence comes from the precision filter, not the LLM]])
- Drop findings below the threshold

**Threshold:** tuned, not fixed. The [[Eval Harness]] sweeps thresholds and produces a precision-recall curve; the chosen threshold maximises precision subject to recall staying above a floor. Configurable. The default gets its own ADR once real data exists.

**Base models:** `microsoft/codebert-base` and `deberta-v3-small`. Both are tried; the comparison is reported as a row in the [[Ablation Table]].

**Training labels** ([[ADR-017 Dev-split-only training data for the precision filter]])
1. Manual labeling of findings from dev-split runs
2. LLM-assisted pre-labeling with human verification
3. Later, a small pilot of real outcome signals ([[ADR-011 Finding outcomes as precision-filter labels]])

**Hard rule:** trained only on dev-split findings, never holdout. `training/build_training_set.py` rejects any case ID present in the holdout split ([[Benchmark Leakage]]).

**Inputs:** findings ([[Finding Schema]]) from the [[Review Graph]], after [[Guardrails]] validation.
**Outputs:** filtered findings with confidence set, posted by [[GitHub Integration]].

**Built for v1 (M5, ADR-030, 2026-10-29), not wired into posting:**
- **Labels:** automatic and location-based, from the findings cached by the dev runs (v1, its rerun, v2). A finding is real if it lies within ±3 lines of a strict bug-holding range of a buggy case (the headline precision test). It is noise if it is on a clean case, or off-range on a buggy case. This replaces manual labelling for v1. A correct finding about an unlabelled issue counts as noise.
- **Models compared:** a feature-based logistic regression (the reference) and `microsoft/codebert-base`, both frozen (embeddings plus a linear head) and fine-tuned. Folds are grouped by case ID, and the thresholds are chosen per outer fold on inner out-of-fold scores, so every reported number is out of fold.
- **Result:** [[precision-filter-dev-2026-10-29]].
- `deberta-v3-small` is not tried in v1.

**Code location:** `training/build_training_set.py`, `training/train_filter.py`, `evals/filter_eval.py`; inference in `app/filter/` once wired.

**Planned code location (original spec):** `app/filter/` (inference); `training/label_findings.py`, `training/build_training_set.py`, `training/train_filter.py` (training).

**Dependencies:** [[transformers]], [[Finding Schema]], [[Storage]] (outcome signals). Decision: [[ADR-008 Encoder classifier as precision filter]].
