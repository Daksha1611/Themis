---
type: decision
status: done
tags: [decision]
related:
  - "[[Operational Monitoring]]"
  - "[[Prometheus]]"
  - "[[Grafana]]"
  - "[[Tracing]]"
  - "[[Hosting]]"
  - "[[Prior Art]]"
---


# ADR-010 Prometheus and Grafana operational metrics

**Status:** accepted

## Context
[[Tracing]] (Langfuse) covers LLM calls, not the health of the running service: queue depth, job latency, webhook and worker errors. Proposed from [[Prior Art]].

## Decision
[[Prometheus]] collects operational metrics from the running service; [[Grafana]] visualises them. See [[Operational Monitoring]].

## Alternatives considered
- Langfuse only: it does not measure service health.

## Consequences
- Two more services in `infra/` docker-compose, and more to host ([[Hosting]]).
- Service processes must expose metrics (design not yet decided, see [[Open Questions]]).
- Must not delay the milestones ([[Scope Creep]]).
