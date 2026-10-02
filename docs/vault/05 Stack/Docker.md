---
name: Docker
description: "Docker and Compose: run the api, worker, Redis, PostgreSQL and Qdrant."
type: tech
status: done
tags: [tech]
related:
  - "[[ADR-010 Prometheus and Grafana operational metrics]]"
  - "[[Webhook Service]]"
  - "[[Job Queue]]"
  - "[[Storage]]"
  - "[[Hosting]]"
version: "Docker 29.7.1, Compose v5.3.1 (local dev machine)"
---

# Docker

**What it is:** Container platform.

**What it does in Themis:** Dockerfile and docker-compose (api, worker, redis, qdrant, postgres) in `infra/`. Prometheus and Grafana are deferred to post-v1 ([[ADR-010 Prometheus and Grafana operational metrics]] superseded). Compose runs on a VPS behind [[Caddy]] ([[ADR-018 Paid VPS over free tier hosting]]).

**Used by:** [[Webhook Service]], [[Job Queue]], [[Storage]], [[Hosting]]

**Version:** Docker 29.7.1, Compose v5.3.1 (local dev machine) (recorded 2026-09-29).
