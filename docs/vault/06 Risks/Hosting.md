---
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

**Affects:** [[Webhook Service]], [[Docker]]
