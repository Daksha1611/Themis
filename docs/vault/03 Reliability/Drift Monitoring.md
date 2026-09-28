---
type: reliability
status: planned
tags: [reliability]
related:
  - "[[Eval Harness]]"
  - "[[LLM Client]]"
  - "[[Metrics]]"
  - "[[ADR-005 LiteLLM via OpenRouter]]"
  - "[[Eval Cost]]"
---

# Drift Monitoring

**Purpose:** detect quality changes across LLM providers and model versions over time.

- Scheduled [[Eval Harness]] runs comparing providers and model versions via the [[LLM Client]]

**Planned code location:** not specified in the planned repo structure. Schedule not specified.

Enabled by [[ADR-005 LiteLLM via OpenRouter]] (model choice is configuration). Risk: [[Eval Cost]].
