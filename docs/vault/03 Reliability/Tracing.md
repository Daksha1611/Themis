---
type: reliability
status: in-progress
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

Decision: [[ADR-006 Langfuse tracing]]. Langfuse is the only v1 source of latency, cost, and token metrics; a separate metrics stack ([[Operational Monitoring]]) is deferred to post-v1.
