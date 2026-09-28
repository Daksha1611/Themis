---
type: reliability
status: planned
tags: [reliability]
related:
  - "[[Eval Harness]]"
  - "[[LLM Client]]"
  - "[[Metrics]]"
  - "[[Storage]]"
  - "[[GitHub Actions]]"
  - "[[ADR-005 LiteLLM via OpenRouter]]"
  - "[[Eval Cost]]"
---

# Drift Monitoring

**Purpose:** detect quality changes across LLM providers and model versions over time.

- **Weekly**, on the same fixed subset of dev cases used by the [[CI Quality Gate]]
- Compares the models actually in use, plus one cheaper and one stronger alternative, via the [[LLM Client]]
- **Output:** a chart over time of quality and cost per model
- Results go to the separate eval database in [[Storage]]

**Planned code location:** `evals/drift/` plus a scheduled [[GitHub Actions]] workflow. Not application code: it runs the [[Eval Harness]] on a schedule.

Enabled by [[ADR-005 LiteLLM via OpenRouter]] (model choice is configuration). Risk: [[Eval Cost]].
