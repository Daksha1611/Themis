---
type: tech
status: in-progress
tags: [tech]
related:
  - "[[LLM Client]]"
  - "[[OpenRouter]]"
  - "[[ADR-005 LiteLLM via OpenRouter]]"
version: 1.103.1
---

# LiteLLM

**What it is:** Python library giving one interface to many LLM providers.

**What it does in Themis:** The LLM client library.

**Used by:** [[LLM Client]], [[OpenRouter]], [[ADR-005 LiteLLM via OpenRouter]]

**Version:** 1.103.1 (installed 2026-09-30).

Called as `litellm.acompletion(model="openrouter/<model>", api_key=...)`. `LITELLM_LOCAL_MODEL_COST_MAP=True` makes it use the cost map bundled with this version (no network fetch at import, reproducible costs). Its specific exceptions (auth, rate limit, timeout, ...) are **not** subclasses of `litellm.exceptions.APIError`; all share `openai.APIError`.

Per the installed 1.103.1 source, `groq/`, `gemini/`, `mistral/` and `openrouter/` prefixes route to each provider's API, and an `api_key` passed per call takes precedence over the provider's environment variable ([[ADR-021 Free-tier four-provider LLM cascade]]).
