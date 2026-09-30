---
type: tech
status: in-progress
tags: [tech]
related:
  - "[[LLM Client]]"
  - "[[LiteLLM]]"
  - "[[ADR-005 LiteLLM via OpenRouter]]"
version: API v1 (https://openrouter.ai/api/v1)
---

# OpenRouter

**What it is:** Hosted API that routes requests to many LLM providers.

**What it does in Themis:** Provider routing for all LLM calls.

**Used by:** [[LLM Client]], [[LiteLLM]], [[ADR-005 LiteLLM via OpenRouter]]

**Version:** API v1 (https://openrouter.ai/api/v1) (installed 2026-09-30).

Development default model: `openai/gpt-4o-mini`, the cheapest model that can produce valid structured output for baseline measurement. Configured via `LLM_MODEL`.
