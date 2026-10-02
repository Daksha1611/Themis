---
name: pydantic-settings
description: "pydantic-settings: loads all configuration from environment variables."
type: tech
status: done
tags: [tech]
related:
  - "[[Webhook Service]]"
  - "[[Job Queue]]"
  - "[[ADR-020 M1 runtime dependencies]]"
version: 2.15.0
---

# pydantic-settings

**What it is:** Settings management built on Pydantic.

**What it does in Themis:** Loads every config value from environment variables (`app/config.py`).

**Used by:** [[Webhook Service]], [[Job Queue]], [[ADR-020 M1 runtime dependencies]]

**Version:** 2.15.0 (installed 2026-09-29).
