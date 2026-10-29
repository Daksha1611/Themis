---
name: ADR-031 Consistency-based precision filter
description: "Decision: the precision filter scores findings by agreement across independent review samples, not by an encoder over the finding; supersedes ADR-008. Gated on a measured cut in clean flags; on the cached dev runs the gate is not yet met."
type: decision
status: accepted
tags: [decision]
related:
  - "[[Precision Filter]]"
  - "[[ADR-008 Encoder classifier as precision filter]]"
  - "[[ADR-016 Confidence comes from the precision filter, not the LLM]]"
  - "[[ADR-029 Aggregated evaluation]]"
  - "[[ADR-030 v1 finish plan and scope cuts]]"
  - "[[precision-filter-dev-2026-10-29]]"
  - "[[agreement-dev-2026-10-29]]"
---

# ADR-031 Consistency-based precision filter

Owner decision, 2026-10-29. Supersedes the encoder approach of [[ADR-008 Encoder classifier as precision filter]]. [[ADR-016 Confidence comes from the precision filter, not the LLM]] stands: `confidence` comes from the filter, never from the LLM's self-report.

## Context
- **Finding-level classifiers do not separate real from noise.** A feature-based logistic regression reached an out-of-fold ROC AUC of 0.664, CodeBERT frozen 0.626 and CodeBERT fine-tuned 0.601 ([[precision-filter-dev-2026-10-29]]). Findings on clean cases scored as high as findings on buggy cases (mean 0.671 vs 0.650).
  - **Cause 1:** the features describe the finding, not whether its claim about the code is true.
  - **Cause 2:** the location-based labels are noisy.
- **CodeBERT work stops.** Fine-tuning also exhausted the machine's memory.
- **The alternative signal is consistency.** The reviewer's output differs from run to run ([[ADR-029 Aggregated evaluation]]). A finding repeated across independent samples may be more likely to be real than a one-off.

## Decision
- **The filter scores findings by agreement across k independent review samples of the same PR.**
  - Findings are matched across samples: same file, lines within ±3, same category.
  - Each merged finding carries its agreement count.
  - `confidence` comes from a small calibrated model on agreement count, category and severity, cross-validated grouped by case, with the Q17 threshold sweep.
- **Build gate:** the filter is built (`app/filter/consistency.py`, production setting `REVIEW_SAMPLES`, default 3, samples in parallel, about 3× cost per PR) only if a voting rule cuts the clean flag rate materially (paired 95% CI below zero) while detection stays within 5 points of a single run.
- **Without separation,** the next candidate is a verifier pass: a second LLM call per finding that must confirm or refute it from the code. It costs quota and needs the owner's decision.
- **Placement:** the filter is wired into posting only after the M4 runs close, alongside M6 ([[Roadmap]]).

## Step 1 result, 2026-10-29 ([[agreement-dev-2026-10-29]], cached runs, no LLM calls)
- **Agreement does carry signal.**
  - **Strict matching, three runs:** 80% of real findings were repeated by at least one other run, against 54% of noise findings.
  - **Location matching:** 84% of real findings appear in all three runs, against 41% of noise findings.
- **The gate is not met.**
  - **Strict, ≥ 2 of 3:** the closest rule. Clean flags −4.3 net cases (95% CI −8.3 to −0.3, p = 0.058); detection −5.3 (−6.7 points, beyond the 5-point limit); J 0.383 → 0.422.
  - **Location, ≥ 3 of 3:** J 0.481 (clean flag rate 24%), but detection −15 points.
  - **Location, ≥ 2 of 2 (v1 + rerun):** J 0.495, but detection −8.7 points.
- **Evidence quality:**
  - **The k = 2 identical-configuration pair is the cleaner evidence:** its disagreement is pure sampling noise.
  - **The k = 3 analysis mixes prompt formats:** v2 numbers the diff and v1 does not, so their line coordinates differ.
  - **Definitive:** the same analysis on the three identical-configuration baseline-arm runs (v2 plus runs 2 and 3), noted in `evals/plans/m4.yaml`.

## Alternatives considered
- **Continue with encoders:** no separation on these data, and memory-bound on this machine.
- **The verifier pass:** costs a second LLM call per finding, on a free-tier quota already committed to the M4 runs.
- **Majority vote without a calibrated model:** used as the Step 1 test; the calibrated model can trade detection against precision more finely.

## Consequences
- **k = 3 samples cost about 3× per PR,** within the ≤ 3× cost target.
- **The filter's decision waits for the baseline arm** of the M4 plan, unless the owner decides otherwise.
- **The filter changes no prompt,** so its code can be built off the review path while the M4 runs are open.
