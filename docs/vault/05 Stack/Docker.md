---
type: tech
status: planned
tags: [tech]
related:
  - "[[Webhook Service]]"
  - "[[Job Queue]]"
  - "[[Storage]]"
  - "[[Hosting]]"
version:
  - "[[ADR-010 Prometheus and Grafana operational metrics]]"
---

# Docker

**What it is:** Container platform.

**What it does in Themis:** Dockerfile and docker-compose (api, worker, redis, qdrant, postgres) in `infra/`. Prometheus and Grafana are deferred to post-v1 ([[ADR-010 Prometheus and Grafana operational metrics]] superseded). Compose runs on a VPS behind [[Caddy]] ([[ADR-018 Paid VPS over free tier hosting]]).

**Used by:** [[Webhook Service]], [[Job Queue]], [[Storage]], [[Hosting]]

**Version:** not installed yet.
