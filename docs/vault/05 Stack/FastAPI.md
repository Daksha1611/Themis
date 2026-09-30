---
type: tech
status: in-progress
tags: [tech]
related:
  - "[[Webhook Service]]"
version: 0.141.1
---

# FastAPI

**What it is:** Python web framework.

**What it does in Themis:** Receives GitHub webhooks and serves health endpoints.

**Used by:** [[Webhook Service]]

**Version:** 0.141.1 (recorded 2026-09-29).

`fastapi==0.141.1` and `starlette==1.7.0` are pinned until the TestClient migration (Q47).
