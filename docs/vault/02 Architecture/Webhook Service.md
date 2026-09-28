---
type: component
status: planned
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
- Serve health endpoints

**Inputs:** GitHub PR webhook POST requests.
**Outputs:** an immediate HTTP response to GitHub; a review job on the [[Job Queue]].

**Planned code location:** `app/api/` (webhook + health endpoints). GitHub App auth belongs to [[GitHub Integration]].

**Dependencies:** [[Job Queue]], [[FastAPI]], [[Python]]. Decisions: [[ADR-003 arq + Redis queue]], [[ADR-018 Paid VPS over free tier hosting]]. Risk: [[Hosting]] (needs an always-on server).
