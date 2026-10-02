---
name: Hosting
description: "Risk that the webhook has no always-on server."
type: risk
status: planned
tags: [risk]
related:
  - "[[Webhook Service]]"
  - "[[Docker]]"
  - "[[ADR-018 Paid VPS over free tier hosting]]"
  - "[[Caddy]]"
---

# Hosting

**Risk:** The [[Webhook Service]] needs an always-on server.

**Mitigation**
- Host chosen: a small paid VPS with Docker Compose and [[Caddy]] ([[ADR-018 Paid VPS over free tier hosting]])
- Keep the deployment live

Not in place yet: the VPS is not provisioned, so the webhook is reached through a quick tunnel during development (Q52b).

**Affects:** [[Webhook Service]], [[Docker]]
