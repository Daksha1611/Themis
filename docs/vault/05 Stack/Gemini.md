---
type: tech
status: in-progress
tags: [tech]
related:
  - "[[LLM Client]]"
  - "[[ADR-021 Free-tier four-provider LLM cascade]]"
  - "[[LiteLLM]]"
version: model gemini-3.5-flash (API v1beta)
---

# Gemini

**What it is:** Google's Gemini API (AI Studio keys), with a free usage tier.

**What it does in Themis:** Second provider in the LLM cascade. LiteLLM prefix `gemini/`, key `GEMINI_API_KEY`.

**Model:** `gemini-3.5-flash`. Chosen 2026-10-01: a pinned, non-preview name (unlike the moving alias `gemini-flash-latest`); returned a valid JSON array (fenced in ```` ```json ````, which the parser strips), but took 51 s. `gemini-2.5-flash` was still listed by the models API but returned 404.

**Free tier:** per-model limits are shown only in AI Studio for the project, not in the public docs; RPD resets at midnight Pacific. LiteLLM warns that `temperature` is planned for removal for Gemini 3+.

**Used by:** [[LLM Client]], [[ADR-021 Free-tier four-provider LLM cascade]]

**Version:** model gemini-3.5-flash (API v1beta).
