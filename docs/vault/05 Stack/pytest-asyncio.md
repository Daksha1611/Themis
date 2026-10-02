---
name: pytest-asyncio
description: "pytest-asyncio: runs async tests under pytest, in auto mode."
type: tech
status: done
tags: [tech]
related:
  - "[[pytest]]"
  - "[[CI Quality Gate]]"
  - "[[GitHub Actions]]"
version: "1.4.0"
---

# pytest-asyncio

**What it is:** pytest plugin for testing `async` code.

**What it does in Themis:** Runs the async tests (worker, LLM client, GitHub calls). `asyncio_mode = "auto"` in `pyproject.toml`, so async test functions need no marker.

**Used by:** [[pytest]], [[CI Quality Gate]], [[GitHub Actions]]

**Version:** 1.4.0 (read with `uv pip show`, 2026-10-02). Installed with the `dev` extra.
