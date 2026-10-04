---
name: Review Graph
description: "Produces structured findings: a single baseline LLM pass today, a LangGraph bug pass and security pass later."
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

**Built (M2):** `app/graph/baseline.py` holds a single baseline pass: one LLM call over the raw diff, covering both logic bugs and security with every allowed category listed in the prompt; no LangGraph, no repo context, no guardrails. It produces the baseline row of the [[Ablation Table]] and is what the [[Eval Harness]] calls. Since [[ADR-026 Numbered diffs and validated output]], the prompt carries a numbered diff (new-file line numbers), findings outside every hunk are dropped (`invalid_line`), and an invalid response gets one retry with the errors fed back. Details: `docs/flow.md` section 4.

**Planned code location:** `app/graph/` (bug pass, security pass, merge nodes).

**Dependencies:** [[LangGraph]], [[LLM Client]], [[Finding Schema]]. Every node's input/output is recorded by [[Tracing]]. Decision: [[ADR-002 Bugs and security only]].
