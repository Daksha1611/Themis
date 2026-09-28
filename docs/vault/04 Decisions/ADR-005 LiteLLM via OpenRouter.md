---
type: decision
status: accepted
tags: [decision]
related:
  - "[[LLM Client]]"
  - "[[LiteLLM]]"
  - "[[OpenRouter]]"
  - "[[Drift Monitoring]]"
  - "[[Eval Cost]]"
---

# ADR-005 LiteLLM via OpenRouter

## Context
Themis needs to compare models and use a cheap model during development.

## Decision
The [[LLM Client]] uses [[LiteLLM]] routed through [[OpenRouter]]. Model choice is configuration.

## Alternatives considered
- None stated in the spec.

## Consequences
- Enables [[Drift Monitoring]] across providers and model versions.
- Supports the cheap-model mitigation for [[Eval Cost]].
