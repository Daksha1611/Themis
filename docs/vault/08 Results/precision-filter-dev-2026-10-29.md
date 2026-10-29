---
name: precision-filter-dev-2026-10-29
description: "M5 precision filter on the cached dev runs (v1, v1 rerun, v2), out of fold: models compared, threshold sweep, filtered metrics with the ADR-029 tests."
type: reliability
status: done
tags: [reliability, results]
related:
  - "[[Precision Filter]]"
  - "[[ADR-030 v1 finish plan and scope cuts]]"
  - "[[ADR-029 Aggregated evaluation]]"
  - "[[ADR-017 Dev-split-only training data for the precision filter]]"
---

# Precision filter, dev split (2026-10-29)

Built from the findings already cached by three dev runs; **no LLM calls**. Holdout never touched (`training/build_training_set.py` rejects holdout case IDs). Every number below is **out of fold**: the model and the threshold applied to a case never saw that case.

## Training set
- **349 findings** from runs v1, v1 rerun and v2 over the 121 scored dev cases: 231 real, 118 noise (74 on clean cases, 44 off-range on buggy cases).
- **Label rule** (location-v1: real = within ±3 of a strict bug-holding range of a buggy case): the same test as the headline precision. **Limitation:** the labels are location-based, so a correct finding about an issue nobody labelled counts as noise, and a wrong finding that happens to sit inside a bug-holding range counts as real.
- **Folds:** 5, grouped by case ID (seeded, buggy and clean dealt separately), so a case's findings from different runs never sit in both train and test.

## Models (out-of-fold ranking quality)

| Model | ROC AUC | Average precision | Base rate (share real) |
|---|---|---|---|
| features | 0.664 | 0.752 | 0.662 |
| codebert | 0.626 | 0.724 | 0.662 |
| codebert, fine-tuned (ranking only) | 0.601 | 0.682 | 0.662 |

- **features:** logistic regression over category, severity, `raw_llm_confidence`, message and suggestion length, span, changed line vs context, hunk size and diff size.
- **codebert:** frozen `microsoft/codebert-base` embeddings (mean-pooled, CPU, 256 tokens) of the finding text plus its diff snippet, with a logistic-regression head.
- Both: standardised inputs; C chosen by grouped inner CV on average precision.
- **codebert, fine-tuned:** `microsoft/codebert-base` with a classification head, trained end to end on each outer fold's training cases (3 epochs, AdamW 2e-5, batch 8, CPU). Only its ranking is compared: choosing its thresholds would take inner fine-tunes per fold, which was not worth running unless it out-ranked the reference.
- **Kept: features** (higher out-of-fold average precision).

## Threshold (Q17)
Chosen inside each outer fold on the training folds' inner out-of-fold scores: the highest pooled precision whose detection rate stays within 5 points of unfiltered. Per-fold thresholds: 0.214, 0.008, 0.167, 0.227, 0.263.

Global sweep over the out-of-fold scores of **features** (pooled over the three runs; detection and clean flags averaged over runs):

| Threshold | Precision | Detection | Clean flag rate | Findings kept |
|---|---|---|---|---|
| 0.0 | 66.2% | 87.9% | 49.6% | 100.0% |
| 0.2 | 72.1% | 82.1% | 48.8% | 89.4% |
| 0.3 | 73.4% | 80.8% | 47.2% | 87.1% |
| 0.4 | 74.6% | 77.5% | 43.1% | 81.4% |
| 0.5 | 74.3% | 74.2% | 41.5% | 75.9% |
| 0.6 | 75.3% | 67.9% | 35.8% | 67.3% |
| 0.7 | 75.6% | 58.3% | 32.5% | 56.4% |
| 0.8 | 74.4% | 35.8% | 22.0% | 34.7% |

## Filtered vs unfiltered, per run

| Run | J | Precision | Clean flag rate | Strict category-correct | Detection |
|---|---|---|---|---|---|
| v1 | 0.435 → 0.373 | 74/108 → 73/94 | 17/41 → 17/41 | 41/80 → 41/80 | 68/80 → 63/80 |
| v1-rerun | 0.388 → 0.300 | 74/117 → 72/105 | 21/41 → 21/41 | 36/80 → 36/80 | 72/80 → 65/80 |
| v2 | 0.327 → 0.326 | 83/124 → 81/116 | 23/41 → 22/41 | 41/80 → 41/80 | 71/80 → 69/80 |

**k-averaged (k = 3):** J 0.383 → 0.333; precision 66.2% → 72.0%; clean flag rate 49.6% → 48.8%; strict category-correct 49.2% → 49.2%; detection 87.9% → 82.1%. Findings dropped: 34 of 349.

## Paired comparison (ADR-029)
Per-case means over the three runs, filtered minus unfiltered; net cases with a bootstrap 95% CI and a two-sided sign-flip permutation p-value.

| Measure | Cases | Unfiltered (sum of means) | Filtered | Net cases (95% CI) | p |
|---|---|---|---|---|---|
| Detection (buggy) | 80 | 70.33 | 65.67 | -4.67 (-8.00 to -2.00) | 0.0012 |
| Strict category-correct | 80 | 39.33 | 39.33 | +0.00 (+0.00 to +0.00) | 1.0000 |
| Clean flags | 41 | 20.33 | 20.00 | -0.33 (-1.00 to +0.00) | 1.0000 |

## Verdict
- **Encoder vs reference:** the kept model is **features**. CodeBERT, frozen or fine-tuned, does not out-rank the feature model on these data. That is a valid result: with a few hundred location-labelled findings, the encoder has too little signal to learn from.
- **J falls by 0.050** (k-averaged). Precision rises because the filter drops findings, mostly on buggy cases; clean flags change by -0.33 cases (p = 1.00).
- **Detection falls 5.8 points** out of fold, against the 5-point limit the thresholds were chosen for on the training folds: the thresholds do not transfer exactly across folds.
- **Not to be wired in this form.** The filter's purpose is to cut clean-case noise (the clean flag rate), and here it does not. Most flagged clean cases rest on a single finding (48 of 61 flagged clean case-runs), so one dropped finding would unflag them; but the model scores findings on clean cases about as high as findings on buggy cases (mean 0.671 vs 0.650), so the thresholds keep them. The features describe the finding, not whether the code is wrong.

## Caveats
- **Not wired into posting.** The filter only sets `confidence` in this evaluation.
- **Location-based labels** (above). The filter learns what the location test counts, including its blind spots.
- **Training findings come from the same three runs that are evaluated.** Out-of-fold scoring keeps every case's own findings out of its model, but the runs share prompts, so this is not a test on new reviewer output. The M4 runs will provide fresh findings to check against.
- **Small data:** a few hundred findings from about a hundred cases; the fold-to-fold thresholds vary.
