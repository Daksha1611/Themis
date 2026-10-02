---
name: ADR-006 Langfuse tracing
description: "Decision: Langfuse traces tokens, cost, latency and node inputs and outputs from day one."
type: decision
status: accepted
tags: [decision]
related:
  - "[[Tracing]]"
  - "[[Langfuse]]"
  - "[[Review Graph]]"
---

# ADR-006 Langfuse tracing

## Context
Every design decision must be backed by numbers, including cost and latency.

## Decision
[[Langfuse]] (OpenTelemetry-compatible) is used for [[Tracing]], on from day one. It logs tokens, cost, latency, and every graph node's input/output.

## Alternatives considered
- None stated in the spec.

## Consequences
- Every [[Review Graph]] node must be traced from the first version of the code.
