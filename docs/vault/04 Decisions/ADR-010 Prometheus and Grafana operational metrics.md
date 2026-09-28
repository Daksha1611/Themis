---
type: decision
status: accepted
tags: [decision]
related:
  - "[[Operational Monitoring]]"
  - "[[Prometheus]]"
  - "[[Grafana]]"
  - "[[Tracing]]"
  - "[[Hosting]]"
  - "[[Prior Art]]"
  - "[[Langfuse]]"
  - "[[Scope Creep]]"
---


# ADR-010 Prometheus and Grafana operational metrics

## Context
[[Tracing]] (Langfuse) covers LLM calls, not the health of the running service: queue depth, job latency, webhook and worker errors. Proposed from [[Prior Art]].

## Decision
[[Prometheus]] collects operational metrics from the running service; [[Grafana]] visualises them. See [[Operational Monitoring]].

## Alternatives considered
- Langfuse only: it does not measure service health.

## Consequences
- Two more services in `infra/` docker-compose, and more to host ([[Hosting]]).
- Service processes must expose metrics (see worker metrics below).
- Must not delay the milestones ([[Scope Creep]]).

## Reconsideration (Q41): awaiting decision
**Recommended:** mark this ADR `superseded` for v1 and move it to a post-v1 stretch goal.
- [[Langfuse]] already provides latency, cost, and token metrics: most of what these dashboards would show.
- A metrics stack adds two Compose services, the worker instrumentation problem below, and dashboard work, all overlapping what exists.
- This is what [[Scope Creep]] warns against.

**If kept instead:** scope is limited to four panels (review throughput, error rate, p95 latency, cost per PR) and one alert (webhook failure rate).

## Worker metrics (Q40): applies only if this ADR survives Q41
An arq worker has no HTTP server, so it cannot expose a scrape endpoint the normal way. Options:
- A small side HTTP server inside the worker process
- A Prometheus Pushgateway

Gotcha: when metrics come from more than one process, `prometheus_client` needs multiprocess mode (a shared directory set by the `PROMETHEUS_MULTIPROC_DIR` environment variable, and a multiprocess collector on the scrape endpoint). Verify against the installed version before use.
