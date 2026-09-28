---
type: component
status: planned
tags: [component]
related:
  - "[[Webhook Service]]"
  - "[[Job Queue]]"
  - "[[Context Builder]]"
  - "[[Precision Filter]]"
  - "[[Guardrails]]"
  - "[[Storage]]"
  - "[[ADR-011 Finding outcomes as precision-filter labels]]"
---

# GitHub Integration

**Purpose:** own every call Themis makes to GitHub.

**Responsibilities**
- GitHub App authentication (JWT → installation token)
- Fetch PR diffs for the [[Context Builder]]
- Post review comments with the filtered findings from the [[Precision Filter]]
- Post the single [[Guardrails]] notice when suspicious instruction-like content is detected
- Read finding-outcome signals (later commits, thread resolution, reactions) for [[ADR-011 Finding outcomes as precision-filter labels]]

**Inputs:** PR identity from the [[Job Queue]]; findings to post.
**Outputs:** PR diffs; posted review comments; outcome signals stored in [[Storage]].

**Planned code location:** `app/github/`.

**Dependencies:** GitHub App credentials. Webhook signature verification stays in the [[Webhook Service]].
