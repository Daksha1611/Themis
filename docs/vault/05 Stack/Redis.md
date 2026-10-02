---
name: Redis
description: "Redis: backing store for the arq job queue."
type: tech
status: done
tags: [tech]
related:
  - "[[Job Queue]]"
  - "[[arq]]"
  - "[[ADR-003 arq + Redis queue]]"
version: server image redis:7-alpine; client redis-py 5.3.1
---

# Redis

**What it is:** In-memory data store.

**What it does in Themis:** Backing store for the arq job queue.

**Used by:** [[Job Queue]], [[arq]], [[ADR-003 arq + Redis queue]]

**Version:** server image redis:7-alpine; client redis-py 5.3.1 (recorded 2026-09-29).
