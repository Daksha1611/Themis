---
name: Groq
description: "Groq: first provider in the free-tier LLM cascade."
type: tech
status: done
tags: [tech]
related:
  - "[[LLM Client]]"
  - "[[ADR-021 Free-tier four-provider LLM cascade]]"
  - "[[LiteLLM]]"
version: model openai/gpt-oss-120b (API, unversioned)
---

# Groq

**What it is:** LLM inference provider with a free plan (fast inference on custom hardware).

**What it does in Themis:** First provider in the LLM cascade. LiteLLM prefix `groq/`, key `GROQ_API_KEY`.

**Model:** `openai/gpt-oss-120b` (131K context). Chosen 2026-10-01 from the live model list: the strongest available model; returned a valid JSON array with correct file paths in 1.7 s. `qwen/qwen3.8-27b` also answered but wrote paths as `b/a.py`.

**Free plan (docs, 2026-10-01):** 30 requests/min, 1,000 requests/day, 8K tokens/min, 200K tokens/day for this model. The 8K tokens/min cap means one large-diff prompt can be rejected outright.

**Used by:** [[LLM Client]], [[ADR-021 Free-tier four-provider LLM cascade]]

**Version:** model openai/gpt-oss-120b (API, unversioned).
