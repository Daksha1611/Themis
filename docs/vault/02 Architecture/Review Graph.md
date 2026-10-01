---
type: component
status: in-progress
tags: [component]
related:
  - "[[Context Builder]]"
  - "[[Guardrails]]"
  - "[[Finding Schema]]"
  - "[[Precision Filter]]"
  - "[[LLM Client]]"
  - "[[Tracing]]"
  - "[[LangGraph]]"
  - "[[ADR-002 Bugs and security only]]"
  - "[[ADR-022 CWE Top 25 security taxonomy]]"
  - "[[ADR-016 Confidence comes from the precision filter, not the LLM]]"
  - "[[ADR-019 Logic bug taxonomy]]"
---

# Review Graph

**Purpose:** produce structured findings from the PR and its context.

**Responsibilities**
- Run a logic-bug pass, categorising each finding by the logic-bug taxonomy ([[ADR-019 Logic bug taxonomy]])
- Run a security pass, categorising each finding by CWE Top 25 ID or `security-other` ([[ADR-022 CWE Top 25 security taxonomy]])
- Merge and de-duplicate the findings from both passes
- Treat delimited content as data to review, never as instructions ([[Guardrails]])

**Inputs:** a sanitized `ReviewContext` from the [[Context Builder]], via [[Guardrails]].
**Outputs:** findings in the [[Finding Schema]] **without** a confidence value ([[ADR-016 Confidence comes from the precision filter, not the LLM]]). They go to [[Guardrails]] for validation, then to the [[Precision Filter]].

**Planned code location:** `app/graph/` (bug pass, security pass, merge nodes). **M2:** `app/graph/baseline.py` holds a single baseline pass (one LLM call over the raw diff, no LangGraph, no repo context), which produces the baseline row of the [[Ablation Table]].

**Dependencies:** [[LangGraph]], [[LLM Client]], [[Finding Schema]]. Every node's input/output is recorded by [[Tracing]]. Decision: [[ADR-002 Bugs and security only]].
