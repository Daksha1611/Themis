---
name: httpx
description: "httpx: async HTTP client for every GitHub API call."
type: tech
status: done
tags: [tech]
related:
  - "[[GitHub Integration]]"
  - "[[ADR-020 M1 runtime dependencies]]"
version: 0.28.1
---

# httpx

**What it is:** Async-capable HTTP client for Python.

**What it does in Themis:** All GitHub API calls: installation tokens, diff fetch and review posting, through one shared connection-pooled client.

**Used by:** [[GitHub Integration]], [[ADR-020 M1 runtime dependencies]]

**Version:** 0.28.1 (installed 2026-09-29).
