---
type: decision
status: accepted
tags: [decision]
related:
  - "[[LLM Client]]"
  - "[[Groq]]"
  - "[[Gemini]]"
  - "[[Mistral]]"
  - "[[OpenRouter]]"
  - "[[LiteLLM]]"
  - "[[ADR-005 LiteLLM via OpenRouter]]"
  - "[[Free Tier Throughput]]"
---

# ADR-021 Free-tier four-provider LLM cascade

## Context
Themis runs on **free tiers only: no paid LLM spend, now or later**. A single OpenRouter key could not serve that: OpenRouter's free tier allows roughly 50 requests per day, too tight to be a primary.

The free-tier landscape shifted significantly during this project. Cerebras moved from a no-card free tier to a card-required trial between planning and implementation, and during model selection a listed Gemini model (`gemini-2.5-flash`) returned 404. **This is why providers are configuration rather than code.**

## Decision
[[LLM Client]] tries providers in order from `LLM_PROVIDER_CASCADE`, default:

1. **[[Groq]]**: highest free daily ceiling and fastest inference.
2. **[[Gemini]]**: strong free tier, lower daily cap.
3. **[[Mistral]]**: Codestral is code-specific, a good fit for code review.
4. **[[OpenRouter]]**: last, because its free tier is capped at roughly 50 requests per day.

- Each provider's model comes from `LLM_MODELS` (provider → model ID); the LiteLLM model string is `<provider>/<model>`.
- Each provider's key comes from `<PROVIDER>_API_KEY`. An empty key means "skip this provider"; any subset of keys works.
- Any provider error moves on to the next provider; `LLMError` is raised only when all have failed, naming each provider and the reason.
- Every response and trace records which `provider` answered.

Adding, removing or reordering a provider is a configuration change, never a code change.

Models chosen on 2026-10-01 from each provider's live model list and a live test call: Groq `openai/gpt-oss-120b`, Gemini `gemini-3.5-flash`, Mistral `codestral-2508`, OpenRouter `qwen/qwen3.8-27b:free`.

## Alternatives considered
- A single paid provider: ruled out by the free-tier-only constraint.
- Supersedes the single-model OpenRouter setup of M2 (the routing mechanism of [[ADR-005 LiteLLM via OpenRouter]], LiteLLM, is unchanged).

## Consequences
- Results can come from different models run to run; `provider` and `model` are recorded on every response and trace so evals can stratify.
- Throughput is bounded by free-tier caps ([[Free Tier Throughput]]).
- `cost_usd` is LiteLLM's **list-price estimate**, so cost-per-PR stays meaningful; actual spend is $0.
- Free tiers may use submitted prompts for training; diffs are not masked yet (Q49).
