---
name: FastAPI
description: "FastAPI: web framework for the webhook and health endpoints."
type: tech
status: done
tags: [tech]
related:
  - "[[Webhook Service]]"
  - "[[starlette]]"
version: 0.141.1
---

# FastAPI

**What it is:** Python web framework.

**What it does in Themis:** Receives GitHub webhooks and serves health endpoints.

**Used by:** [[Webhook Service]]

**Version:** 0.141.1 (recorded 2026-09-29).

`fastapi==0.141.1` and `starlette==1.7.0` ([[starlette]]) are pinned until the TestClient migration (Q47).
