---
name: starlette
description: "Starlette: the ASGI toolkit under FastAPI, pinned directly until the TestClient migration (Q47)."
type: tech
status: done
tags: [tech]
related:
  - "[[FastAPI]]"
  - "[[Webhook Service]]"
  - "[[pytest]]"
version: "1.7.0"
---

# starlette

**What it is:** ASGI framework and toolkit; FastAPI is built on it.

**What it does in Themis:** Request handling under [[FastAPI]] for the [[Webhook Service]]. Its `TestClient` drives the webhook tests.

**Used by:** [[FastAPI]], [[Webhook Service]], [[pytest]]

**Version:** 1.7.0 (read with `uv pip show`, 2026-10-02). Pinned directly in `pyproject.toml`, with `fastapi`, until the TestClient migration (Q47).
