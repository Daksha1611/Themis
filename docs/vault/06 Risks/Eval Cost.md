---
type: risk
status: planned
tags: [risk]
related:
  - "[[Eval Harness]]"
  - "[[CI Quality Gate]]"
  - "[[Drift Monitoring]]"
  - "[[LLM Client]]"
  - "[[Benchmark]]"
---

# Eval Cost

**Risk:** Running the full review path over the benchmark costs LLM tokens on every run.

**Mitigation**
- Cache LLM responses ([[Eval Harness]])
- Run a fixed 50-case dev subset per PR and the full dev split nightly ([[CI Quality Gate]])
- Drift runs weekly on the same fixed subset ([[Drift Monitoring]])
- Use a cheap model during development ([[LLM Client]])
- Run holdout only at completion ([[Benchmark]])

**Affects:** [[Eval Harness]], [[CI Quality Gate]], [[Drift Monitoring]], [[LLM Client]], [[Benchmark]]
