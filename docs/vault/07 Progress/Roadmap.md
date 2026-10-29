---
name: Roadmap
description: "The three-week plan to finish v1 (ADR-030): what each week delivers."
type: progress
status: in-progress
tags: [progress]
related:
  - "[[ADR-030 v1 finish plan and scope cuts]]"
  - "[[Current Status]]"
  - "[[Session Log]]"
---

# Roadmap

Plan from 2026-10-28 ([[ADR-030 v1 finish plan and scope cuts]]). Quota-bound eval runs go in the background, and the rest of the work proceeds alongside them.

## Week 1 (from 2026-10-28)
- **M4 wired behind `CONTEXT_BUDGET`** (off by default). With the budget at 0, prompts are proved identical to v2's.
- **M4 runs started** with `python -m evals.schedule next` (plan `evals/plans/m4.yaml`): baseline arm = v2 + 2 runs, context arm = 3 runs at 1K.
- **M5 precision filter** built and cross-validated from the cached dev findings (no LLM calls). The encoder approach fails; the pivot is to consistency ([[ADR-031 Consistency-based precision filter]]), and Step 1 does not yet pass its gate ([[agreement-dev-2026-10-29]]).
- README brought up to date.

## Branch rule while the M4 runs are open
The open M4 runs refuse to resume after any change to a review-path module or to the rendered prompts. So:
- **M6 guardrails are built on a separate branch** (they change the prompt) and merged after the M4 runs finish.
- **Wiring the precision filter into posting** waits for the same point, on its own branch, alongside M6.
- **Work off the review path** (`app/filter/`, `evals/`) continues on `main`.

## Week 2
- **The M4 result:** k = 3 per arm, paired permutation test plus bootstrap CI ([[ADR-029 Aggregated evaluation]]), and the falsification split.
- **M6:** guardrails plus the prompt-injection set ([[Guardrails]]), on a separate branch.
- **M7:** a fingerprint-based eval gate with no LLM calls in CI ([[CI Quality Gate]]).
- **Deployment** ([[ADR-018 Paid VPS over free tier hosting]]).

## Week 3
- **Label the holdout,** after prompt tuning is frozen ([[ADR-007 dev-holdout benchmark split]]).
- **The final holdout runs.**
- **Publish the results page.**
- **The demo.**

## Cut from v1
- **The reshaped probe:** cancelled; medium reasoning effort stays.
- **Q58, the security benchmark track:** post-v1.
- **Q48, large PRs:** a documented limitation, not built.
