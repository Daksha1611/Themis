---
name: Operational Monitoring
description: "Service health metrics with Prometheus and Grafana, deferred to post-v1."
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

> **Deferred to post-v1.** Not built in v1: [[ADR-010 Prometheus and Grafana operational metrics]] is superseded. This note is kept as the record for a possible post-v1 reinstatement.

**Purpose:** show whether the running service is healthy.

- [[Prometheus]] collects operational metrics: queue depth, job latency, error rates
- [[Grafana]] dashboards visualise them
- Covers the [[Webhook Service]] and the [[Job Queue]] worker
- Complements [[Tracing]], which covers LLM calls

**If reinstated:** four panels (review throughput, error rate, p95 latency, cost per PR) and one alert (webhook failure rate).

**Planned code location:** Prometheus and Grafana run in `infra/` docker-compose.

Decision: [[ADR-010 Prometheus and Grafana operational metrics]]. Risk: [[Hosting]].
