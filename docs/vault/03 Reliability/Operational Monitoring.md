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

**Purpose:** show whether the running service is healthy.

- [[Prometheus]] collects operational metrics: queue depth, job latency, error rates
- [[Grafana]] dashboards visualise them
- Covers the [[Webhook Service]] and the [[Job Queue]] worker
- Complements [[Tracing]], which covers LLM calls

**Planned code location:** Prometheus and Grafana run in `infra/` docker-compose. How the app exposes metrics is not yet decided.

Decision: [[ADR-010 Prometheus and Grafana operational metrics]]. Risk: [[Hosting]].
