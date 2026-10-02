---
name: Finding Schema
description: "Typed data contracts: Finding, ReviewResult and ReviewContext; confidence versus raw_llm_confidence."
type: component
status: in-progress
tags: [component]
related:
  - "[[Review Graph]]"
  - "[[Context Builder]]"
  - "[[Precision Filter]]"
  - "[[Eval Harness]]"
  - "[[Storage]]"
  - "[[Pydantic]]"
  - "[[ADR-022 CWE Top 25 security taxonomy]]"
  - "[[ADR-016 Confidence comes from the precision filter, not the LLM]]"
  - "[[ADR-019 Logic bug taxonomy]]"
---

# Finding Schema

**Purpose:** make every review artifact a typed object. Never free text.

## `Finding`
Defined in `app/schemas.py` (M2).

| Field | Values |
|---|---|
| file | path |
| line_start, line_end | the line range of the problem (`line_end >= line_start`). A range, not a single line: bug-location matching compares against a labeled range ±3 lines (Q23) |
| category | a logic-bug category ([[ADR-019 Logic bug taxonomy]]), a CWE ID from [[ADR-022 CWE Top 25 security taxonomy]], or `security-other`. **Validated:** any other value fails validation (and becomes a parse error); the allowed set is in `app/taxonomy.py` |
| subcategory | required free text when category is `security-other` |
| severity | `critical` \| `high` \| `medium` \| `low` |
| message | what is wrong, one sentence |
| suggestion | how to fix it, one sentence |
| confidence | float 0.0–1.0, **set by the [[Precision Filter]], never by the LLM** ([[ADR-016 Confidence comes from the precision filter, not the LLM]]). 0.0 until the filter exists (M5) |
| raw_llm_confidence | float 0.0–1.0: what the LLM reported about itself. **Stored and traced, never used for filtering, never shown on the PR** |

### `confidence` vs `raw_llm_confidence`
This split is central to the project's thesis. An LLM's self-reported confidence is poorly calibrated, so Themis never lets it decide what gets posted. The LLM's number is kept as `raw_llm_confidence` so the eval harness can measure how badly calibrated it is; the decision-making `confidence` comes only from the trained precision filter. If the LLM's output includes a `confidence` key, it is discarded.

## `ReviewContext` (planned)
**Not in code yet**: it is defined when the [[Context Builder]] is built. Planned fields:
- `pr_metadata`
- `changed_files`: path, hunks, full file content when small
- `related_chunks`: path, symbol name, code, retrieval score, reason retrieved
- `token_budget_used`

## `ReviewResult`
- `run_id: str`
- `pr_ref: PRRef` (repo, number, head_sha)
- `findings: list[Finding]`
- `raw_finding_count`, `filtered_finding_count` (required to report precision-filter impact; equal until M5)
- `llm_config: LLMConfig` (provider, model, temperature, max_tokens). `provider` names the cascade provider that answered ([[ADR-021 Free-tier four-provider LLM cascade]]), or is None when no LLM call succeeded. `model_config` is reserved by Pydantic v2
- `token_usage: TokenUsage` (prompt_tokens, completion_tokens, total_tokens)
- `cost_usd`, `latency_ms`
- `guardrail_triggered: bool` (always False until guardrails exist)
- `status`: `success` \| `partial` \| `failed`
- `error: str | None`

In M2 the worker builds a `ReviewResult` at the end of every job and records it as the Langfuse trace output ([[Tracing]]). It is not stored whole: [[Storage]] keeps a `review_runs` row with selected fields.

**Used by:** [[Review Graph]], [[Precision Filter]], [[Eval Harness]], [[Storage]].

**Code location:** `app/schemas.py` (`Finding`, `ReviewResult` and its parts, plus the `WebhookPayload` and `ReviewJob` models); the allowed categories in `app/taxonomy.py`.

**Dependencies:** [[Pydantic]].
