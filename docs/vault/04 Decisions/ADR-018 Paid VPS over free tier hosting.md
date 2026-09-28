---
type: decision
status: accepted
tags: [decision]
related:
  - "[[Hosting]]"
  - "[[Webhook Service]]"
  - "[[Docker]]"
  - "[[Caddy]]"
  - "[[Qdrant]]"
  - "[[PostgreSQL]]"
---

# ADR-018 Paid VPS over free tier hosting

## Context
The [[Webhook Service]] needs an always-on server ([[Hosting]]). Free tiers sleep on inactivity, and a sleeping webhook misses GitHub events.

## Decision
A small VPS (Hetzner or DigitalOcean, ~$5–10/month) running [[Docker]] Compose, with [[Caddy]] for TLS.

Optional: managed free tiers for Qdrant Cloud and Neon Postgres to shrink the VPS.

## Alternatives considered
- Free-tier hosting: sleeps on inactivity and misses GitHub events.

## Consequences
- A monthly hosting cost.
- Caddy joins the tech stack.
