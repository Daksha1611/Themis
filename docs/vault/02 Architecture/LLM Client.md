---
type: component
status: planned
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

**Planned code location:** `app/llm.py` (client and model config).

**Dependencies:** [[LiteLLM]], [[OpenRouter]]. Decision: [[ADR-005 LiteLLM via OpenRouter]]. The [[Eval Harness]] caches LLM calls; [[Drift Monitoring]] compares providers and model versions through it. Risk: [[Eval Cost]].
