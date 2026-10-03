---
name: LLM Client
description: "The single path to language models: LiteLLM over the free-tier four-provider cascade."
type: component
status: done
tags: [component]
related:
  - "[[Review Graph]]"
  - "[[Eval Harness]]"
  - "[[Drift Monitoring]]"
  - "[[LiteLLM]]"
  - "[[OpenRouter]]"
  - "[[Groq]]"
  - "[[Gemini]]"
  - "[[Mistral]]"
  - "[[ADR-021 Free-tier four-provider LLM cascade]]"
  - "[[Free Tier Throughput]]"
  - "[[ADR-005 LiteLLM via OpenRouter]]"
  - "[[Eval Cost]]"
---

# LLM Client

**Purpose:** the single path from Themis to language models.

**Responsibilities**
- Call models through [[LiteLLM]], over the free-tier provider cascade ([[ADR-021 Free-tier four-provider LLM cascade]])
- Keep providers and model choice in configuration

**Inputs:** prompts from the [[Review Graph]].
**Outputs:** model responses back to the [[Review Graph]].

**Code location:** `app/llm.py`. `complete(messages, max_tokens=None, temperature=None, pinned=None) → LLMResponse` (content, `provider`, model, prompt/completion/total tokens, `cost_usd`, and `reasoning`: the model's thinking when the provider returns it).

**Pinned mode** ([[ADR-024 Eval runs pin a single provider and model]]): with `pinned=PinnedLLM(provider, model, cache)`, `complete()` makes exactly one attempt on that model and never falls through to the cascade. A failure raises `LLMError` carrying the HTTP status and the provider's message (`detail`). An optional response cache (the `ResponseCache` protocol, implemented by `evals/cache.py`) is consulted first; a hit makes no call. Eval runs only; production keeps the cascade. Configuration: `EVAL_PROVIDER`, `EVAL_MODEL` (default `groq` / `openai/gpt-oss-120b`).

**Provider cascade** ([[ADR-021 Free-tier four-provider LLM cascade]]): free tiers only. Tries `LLM_PROVIDER_CASCADE` in order (default [[Groq]] → [[Gemini]] → [[Mistral]] → [[OpenRouter]]). Per provider: model from `LLM_MODELS`, key from `<PROVIDER>_API_KEY`; an empty key skips the provider without a call; any provider error moves on to the next. `LLMError` only when every provider has failed, naming each and why. The fallback path is logged at DEBUG. Providers are configuration, never code.

**Configuration** (`app/config.py`): `GROQ_API_KEY`, `GEMINI_API_KEY`, `MISTRAL_API_KEY`, `OPENROUTER_API_KEY`, `LLM_PROVIDER_CASCADE` (JSON list), `LLM_MODELS` (JSON object: provider → model ID), `LLM_MAX_TOKENS` (2048), `LLM_TEMPERATURE` (0.0, for eval reproducibility).

**Tracing:** a `llm.complete` span holds one `llm.generate` generation per provider attempted (model, parameters, usage, cost, and `provider` in metadata); the span output names the provider that answered and every attempt.

**Cost:** `cost_usd` is LiteLLM's list-price estimate (actual free-tier spend is $0); 0.0 where LiteLLM has no price.

**Dependencies:** [[LiteLLM]]; providers [[Groq]], [[Gemini]], [[Mistral]], [[OpenRouter]]. Decisions: [[ADR-005 LiteLLM via OpenRouter]] (amended by ADR-021), [[ADR-021 Free-tier four-provider LLM cascade]]. The [[Eval Harness]] calls it in pinned mode with a response cache ([[ADR-024 Eval runs pin a single provider and model]]); [[Drift Monitoring]] compares providers and model versions through it. Risks: [[Eval Cost]], [[Free Tier Throughput]].
