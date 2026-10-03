---
name: ADR-024 Eval runs pin a single provider and model
description: "Decision: eval runs call one pinned provider and model with the cascade disabled; production keeps the cascade."
type: decision
status: accepted
tags: [decision]
related:
  - "[[ADR-021 Free-tier four-provider LLM cascade]]"
  - "[[Eval Harness]]"
  - "[[LLM Client]]"
  - "[[Metrics]]"
  - "[[Free Tier Throughput]]"
---

# ADR-024 Eval runs pin a single provider and model

Refines [[ADR-021 Free-tier four-provider LLM cascade]] for eval runs (owner decision, 2026-10-03).

## Context
The production cascade falls through to the next provider on any failure. If eval runs did the same, one result set would mix models. The baseline would be a blend, and every later ablation comparison would be meaningless.

## Decision
- **Eval mode pins one provider and model** through configuration: `EVAL_PROVIDER`, `EVAL_MODEL`. The default is `groq` + `openai/gpt-oss-120b`, the production primary, so the baseline reflects what production actually runs.
- **No cascade in eval mode.** A rate limit means back off and retry the same model. On persistent limits, the runner checkpoints and stops, so the run resumes later. It never falls through to another provider.
- **Oversized requests are failures, not reroutes.** A case whose request exceeds the pinned model's hard per-request limit is recorded as `failed: provider-limit` and reported.
- **Production is unchanged:** the worker still uses the cascade.
- **One review code path.** `run_baseline_review(diff, pr_metadata, llm=None)` takes an optional `PinnedLLM` (provider, model, optional response cache). The default is the production cascade; the eval runner passes the pinned config. In pinned mode `complete()` makes exactly one attempt on the pinned model; retries and pacing belong to the runner.
- **Provenance:** every results record and run summary stores the provider and model, and the report shows the share of answered cases that came from the pinned model (must be 100%).

## Consequences
- Eval results are attributable to a single model, so comparisons between runs are meaningful.
- A full run is bounded by one model's free-tier budget (Groq: 200K tokens/day, 8K tokens/minute), so it may span days. The response cache and resumable runs make that safe ([[Free Tier Throughput]], [[Eval Harness]]).
