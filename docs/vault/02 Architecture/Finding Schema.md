---
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
  - "[[ADR-009 OWASP Top 10 security taxonomy]]"
  - "[[ADR-016 Confidence comes from the precision filter, not the LLM]]"
  - "[[ADR-019 Logic bug taxonomy]]"
---

# Finding Schema

**Purpose:** make every review artifact a typed object. Never free text.

## `Finding`
| Field | Values |
|---|---|
| file | path |
| line | line number |
| category | a logic-bug category ([[ADR-019 Logic bug taxonomy]]), an OWASP Top 10 (2021) category, or `security-other` ([[ADR-009 OWASP Top 10 security taxonomy]]) |
| subcategory | required free text when category is `security-other` |
| severity | `critical` \| `high` \| `medium` \| `low` |
| message | text |
| confidence | float 0.0–1.0, set by the [[Precision Filter]], never by the LLM ([[ADR-016 Confidence comes from the precision filter, not the LLM]]) |

## `ReviewContext`
Output of the [[Context Builder]]:
- `pr_metadata`
- `changed_files`: path, hunks, full file content when small
- `related_chunks`: path, symbol name, code, retrieval score, reason retrieved
- `token_budget_used`

## `ReviewResult`
- `run_id`
- `pr_ref`: repo, number, head SHA
- `findings: list[Finding]`
- `raw_finding_count`, `filtered_finding_count` (required to report precision-filter impact)
- `llm_config` (the model configuration; `model_config` is reserved by Pydantic v2)
- `token_usage`, `cost_usd`, `latency_ms`
- `guardrail_triggered: bool`
- `status`: `success` \| `partial` \| `failed`
- `error`

**Used by:** [[Review Graph]], [[Precision Filter]], [[Eval Harness]], [[Storage]].

**Planned code location:** `app/schemas.py`.

**Dependencies:** [[Pydantic]].
