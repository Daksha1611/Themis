---
type: tech
status: in-progress
tags: [tech]
related:
  - "[[LLM Client]]"
  - "[[ADR-021 Free-tier four-provider LLM cascade]]"
  - "[[LiteLLM]]"
version: model codestral-2508 (API v1)
---

# Mistral

**What it is:** Mistral AI's API, with a free (experiment) tier.

**What it does in Themis:** Third provider in the LLM cascade. LiteLLM prefix `mistral/`, key `MISTRAL_API_KEY`.

**Model:** `codestral-2508` (pinned rather than `codestral-latest`). Code-specific, a good fit for code review; returned a valid JSON array in 1.6 s. A concurrent test request to `mistral-medium-2604` was rate-limited.

**Used by:** [[LLM Client]], [[ADR-021 Free-tier four-provider LLM cascade]]

**Version:** model codestral-2508 (API v1).
