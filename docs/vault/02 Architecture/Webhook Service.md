---
name: Webhook Service
description: "FastAPI endpoint that verifies GitHub webhooks, filters pull request events and enqueues review jobs."
type: component
status: done
tags: [component]
related:
  - "[[Job Queue]]"
  - "[[GitHub Integration]]"
  - "[[FastAPI]]"
  - "[[Python]]"
  - "[[Hosting]]"
  - "[[ADR-003 arq + Redis queue]]"
  - "[[ADR-018 Paid VPS over free tier hosting]]"
---

# Webhook Service

**Purpose:** receive GitHub pull request events and hand them off without doing the review inline.

**Responsibilities**
- Receive GitHub PR events
- Verify the webhook signature
- Enqueue a review job on the [[Job Queue]]
- Return immediately (GitHub times out slow responses)
- Serve `GET /health`

**Responses** (details in `docs/flow.md` section 1)
- **202** `{"queued": true, "pr": N}`: a `pull_request` event with action `opened` or `synchronize`, enqueued
- **403** `{"error": "invalid signature"}`: signature header missing or wrong
- **200** `{"ignored": true}`: any other event or action (ignoring is not a failed delivery)
- **400** `{"error": "invalid JSON"}` or `{"error": "invalid payload"}`: malformed body, or required fields missing
- **500** `{"error": "could not enqueue job"}` or `{"error": "internal error"}`: Redis or an unexpected error; nothing reaches GitHub as an exception

**Inputs:** GitHub PR webhook POST requests.
**Outputs:** an immediate HTTP response to GitHub; a review job on the [[Job Queue]].

**Code location:** `app/api/webhook.py`, `app/api/health.py`; app factory and lifespan in `app/main.py`. GitHub App auth belongs to [[GitHub Integration]].

**Dependencies:** [[Job Queue]], [[FastAPI]], [[Python]]. Decisions: [[ADR-003 arq + Redis queue]], [[ADR-018 Paid VPS over free tier hosting]]. Risk: [[Hosting]] (needs an always-on server).
