---
name: ADR-005 LiteLLM via OpenRouter
description: "Decision: LiteLLM is the LLM client library; its OpenRouter-only routing is amended by ADR-021."
type: decision
status: accepted
tags: [decision]
related:
  - "[[LLM Client]]"
  - "[[LiteLLM]]"
  - "[[OpenRouter]]"
  - "[[Drift Monitoring]]"
  - "[[Eval Cost]]"
  - "[[ADR-021 Free-tier four-provider LLM cascade]]"
---

# ADR-005 LiteLLM via OpenRouter

> **Amended by [[ADR-021 Free-tier four-provider LLM cascade]] (2026-10-01).** LiteLLM is still the client library and model choice is still configuration. The OpenRouter-only routing is replaced: OpenRouter is now the last of four free-tier providers. The "cheap model during development" context no longer applies, because Themis uses free tiers only.

## Context
Themis needs to compare models and use a cheap model during development.

## Decision
The [[LLM Client]] uses [[LiteLLM]] routed through [[OpenRouter]]. Model choice is configuration.

## Alternatives considered
- None stated in the spec.

## Consequences
- Enables [[Drift Monitoring]] across providers and model versions.
- Supports the cheap-model mitigation for [[Eval Cost]].
