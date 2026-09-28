---
type: reliability
status: planned
tags: [reliability]
related:
  - "[[Webhook Service]]"
  - "[[Job Queue]]"
  - "[[Tracing]]"
  - "[[Prometheus]]"
  - "[[Grafana]]"
  - "[[ADR-010 Prometheus and Grafana operational metrics]]"
  - "[[Hosting]]"
---


# Operational Monitoring

> **Pending decision (Q41):** recommended to be descoped from v1. See [[ADR-010 Prometheus and Grafana operational metrics]].

**Purpose:** show whether the running service is healthy.

- [[Prometheus]] collects operational metrics: queue depth, job latency, error rates
- [[Grafana]] dashboards visualise them
- Covers the [[Webhook Service]] and the [[Job Queue]] worker
- Complements [[Tracing]], which covers LLM calls

**If kept:** four panels (review throughput, error rate, p95 latency, cost per PR) and one alert (webhook failure rate).

**Worker metrics (Q40, only if kept):** the arq worker has no HTTP server. Options: a side HTTP server inside the worker process, or a Pushgateway. `prometheus_client` needs multiprocess mode when metrics come from more than one process.

**Planned code location:** Prometheus and Grafana run in `infra/` docker-compose.

Decision: [[ADR-010 Prometheus and Grafana operational metrics]]. Risk: [[Hosting]].
