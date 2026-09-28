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
---

# Docker

**What it is:** Container platform.

**What it does in Themis:** Dockerfile and docker-compose (api, worker, redis, qdrant, postgres, prometheus, grafana) in `infra/`. Prometheus and Grafana are pending Q41. Compose runs on a VPS behind [[Caddy]] ([[ADR-018 Paid VPS over free tier hosting]]).

**Used by:** [[Webhook Service]], [[Job Queue]], [[Storage]], [[Hosting]]

**Version:** not installed yet.
