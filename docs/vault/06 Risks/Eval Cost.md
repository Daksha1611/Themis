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
- Run only the dev split in the [[CI Quality Gate]]
- Use a cheap model during development ([[LLM Client]])
- Run holdout only at completion ([[Benchmark]])

**Affects:** [[Eval Harness]], [[CI Quality Gate]], [[Drift Monitoring]], [[LLM Client]], [[Benchmark]]
