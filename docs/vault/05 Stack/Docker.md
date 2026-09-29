---
type: tech
status: in-progress
tags: [tech]
related:
  - "[[Webhook Service]]"
  - "[[Job Queue]]"
  - "[[Storage]]"
  - "[[Hosting]]"
version: Docker 29.7.1, Compose v5.3.1 (local dev machine)
  - "[[ADR-010 Prometheus and Grafana operational metrics]]"
---

# Docker

**What it is:** Container platform.

**What it does in Themis:** Dockerfile and docker-compose (api, worker, redis, qdrant, postgres) in `infra/`. Prometheus and Grafana are deferred to post-v1 ([[ADR-010 Prometheus and Grafana operational metrics]] superseded). Compose runs on a VPS behind [[Caddy]] ([[ADR-018 Paid VPS over free tier hosting]]).

**Used by:** [[Webhook Service]], [[Job Queue]], [[Storage]], [[Hosting]]

**Version:** Docker 29.7.1, Compose v5.3.1 (local dev machine) (recorded 2026-09-29).
