---
type: component
status: in-progress
tags: [component]
related:
  - "[[Review Graph]]"
  - "[[Eval Harness]]"
  - "[[Drift Monitoring]]"
  - "[[LiteLLM]]"
  - "[[OpenRouter]]"
  - "[[ADR-005 LiteLLM via OpenRouter]]"
  - "[[Eval Cost]]"
---

# LLM Client

**Purpose:** the single path from Themis to language models.

**Responsibilities**
- Call models through [[LiteLLM]] routed via [[OpenRouter]]
- Keep model choice in configuration

**Inputs:** prompts from the [[Review Graph]].
**Outputs:** model responses back to the [[Review Graph]].

**Code location:** `app/llm.py` (M2). `complete(messages, model=None, max_tokens=None, temperature=None) → LLMResponse` (content, model, prompt/completion/total tokens, `cost_usd`). Calls LiteLLM with `openrouter/<LLM_MODEL>`; cost from LiteLLM's bundled cost map; every failure wrapped in `LLMError(message, status_code)`. Traced as a Langfuse `generation`.

**Configuration** (`app/config.py`): `OPENROUTER_API_KEY`, `LLM_MODEL`, `LLM_MAX_TOKENS` (2048), `LLM_TEMPERATURE` (0.0, for eval reproducibility).

**Development default model:** `openai/gpt-4o-mini`, the cheapest model that can produce valid structured output for baseline measurement. The model is configuration, not code.

**Dependencies:** [[LiteLLM]], [[OpenRouter]]. Decision: [[ADR-005 LiteLLM via OpenRouter]]. The [[Eval Harness]] caches LLM calls; [[Drift Monitoring]] compares providers and model versions through it. Risk: [[Eval Cost]].
