---
type: reliability
status: planned
tags: [reliability]
related:
  - "[[Review Graph]]"
  - "[[LLM Client]]"
  - "[[Langfuse]]"
  - "[[Operational Monitoring]]"
  - "[[ADR-006 Langfuse tracing]]"
  - "[[ADR-013 Langfuse cloud over self-hosting]]"
---

# Tracing

**Purpose:** see what every review did and what it cost.

- Tool: [[Langfuse]] (OpenTelemetry-compatible), cloud free tier ([[ADR-013 Langfuse cloud over self-hosting]])
- On from day one
- Logs tokens, cost, latency, and every [[Review Graph]] node's input/output

**Planned code location:** `app/observability/` (setup and decorators).

Decision: [[ADR-006 Langfuse tracing]]. Service health is covered separately by [[Operational Monitoring]] (pending Q41).
