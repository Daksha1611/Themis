---
type: decision
status: accepted
tags: [decision]
related:
  - "[[Webhook Service]]"
  - "[[Job Queue]]"
  - "[[arq]]"
  - "[[Redis]]"
---

# ADR-003 arq + Redis queue

## Context
GitHub times out slow webhook responses, so the review cannot run inside the webhook request.

## Decision
The [[Webhook Service]] enqueues a job and returns immediately. [[arq]] with [[Redis]] is the [[Job Queue]]; a worker consumes review jobs.

## Alternatives considered
- None stated in the spec.

## Consequences
- Redis is a required runtime service (in `infra/` docker-compose).
- Webhook and worker run as separate processes.
