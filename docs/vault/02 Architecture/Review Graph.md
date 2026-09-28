---
type: component
status: planned
tags: [component]
related:
  - "[[Context Builder]]"
  - "[[Finding Schema]]"
  - "[[Precision Filter]]"
  - "[[LLM Client]]"
  - "[[Guardrails]]"
  - "[[Tracing]]"
  - "[[LangGraph]]"
  - "[[ADR-002 Bugs and security only]]"
  - "[[ADR-009 OWASP Top 10 security taxonomy]]"
---

# Review Graph

**Purpose:** produce structured findings from the PR and its context.

**Responsibilities**
- Run a logic-bug pass
- Run a security pass, classifying each security finding by OWASP Top 10 ([[ADR-009 OWASP Top 10 security taxonomy]])
- Merge and de-duplicate the findings from both passes

**Inputs:** diff and related code from the [[Context Builder]].
**Outputs:** a list of findings in the [[Finding Schema]], passed to the [[Precision Filter]].

**Planned code location:** `app/graph/` (bug pass, security pass, merge nodes).

**Dependencies:** [[LangGraph]], [[LLM Client]], [[Finding Schema]]. Every node's input/output is recorded by [[Tracing]]. Relationship to [[Guardrails]] is not yet specified. Decision: [[ADR-002 Bugs and security only]].
