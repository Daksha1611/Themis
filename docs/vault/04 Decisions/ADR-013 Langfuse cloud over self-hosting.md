---
name: ADR-013 Langfuse cloud over self-hosting
description: "Decision: use the Langfuse cloud free tier instead of self-hosting."
type: decision
status: accepted
tags: [decision]
related:
  - "[[Tracing]]"
  - "[[Langfuse]]"
  - "[[ADR-006 Langfuse tracing]]"
  - "[[Docker]]"
---

# ADR-013 Langfuse cloud over self-hosting

## Context
[[Tracing]] ([[ADR-006 Langfuse tracing]]) needs a Langfuse instance. Self-hosting requires running ClickHouse alongside everything else.

## Decision
Use Langfuse cloud, free tier. Langfuse does not appear in docker-compose.

## Alternatives considered
- Self-hosted Langfuse: high operational cost (ClickHouse), no portfolio benefit.

## Consequences
- No Langfuse or ClickHouse services to run or host.
- Trace data is stored by Langfuse cloud, not on the Themis host.
