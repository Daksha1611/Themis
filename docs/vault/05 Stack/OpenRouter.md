---
type: tech
status: in-progress
tags: [tech]
related:
  - "[[LLM Client]]"
  - "[[ADR-021 Free-tier four-provider LLM cascade]]"
  - "[[LiteLLM]]"
  - "[[ADR-005 LiteLLM via OpenRouter]]"
version: API v1 (https://openrouter.ai/api/v1)
---

# OpenRouter

**What it is:** Hosted API that routes requests to many LLM providers.

**What it does in Themis:** Provider routing for all LLM calls.

**Used by:** [[LLM Client]], [[LiteLLM]], [[ADR-005 LiteLLM via OpenRouter]]

**Version:** API v1 (https://openrouter.ai/api/v1) (installed 2026-09-30).

**Free-tier only (ADR-021):** last provider in the cascade, model `qwen/qwen3.8-27b:free` (chosen 2026-10-01 from the live `:free` model list; valid JSON array in 14.8 s). OpenRouter's free tier allows roughly 50 requests/day. `cohere/north-mini-code:free` returned empty content in the same test.
