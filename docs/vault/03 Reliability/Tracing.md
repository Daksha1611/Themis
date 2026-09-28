---
type: reliability
status: planned
tags: [reliability]
related:
  - "[[Review Graph]]"
  - "[[LLM Client]]"
  - "[[Langfuse]]"
  - "[[ADR-006 Langfuse tracing]]"
  - "[[Operational Monitoring]]"
---

# Tracing

**Purpose:** see what every review did and what it cost.

- Tool: [[Langfuse]] (OpenTelemetry-compatible)
- On from day one
- Logs tokens, cost, latency, and every [[Review Graph]] node's input/output

**Planned code location:** not specified in the planned repo structure.

Decision: [[ADR-006 Langfuse tracing]]. Service health (queue depth, errors) is covered separately by [[Operational Monitoring]].
