---
type: risk
status: planned
tags: [risk]
related:
  - "[[Benchmark]]"
  - "[[Eval Harness]]"
  - "[[CI Quality Gate]]"
  - "[[ADR-021 Free-tier four-provider LLM cascade]]"
  - "[[LLM Client]]"
---

# Free Tier Throughput

**Risk:** free-tier daily request caps constrain how often the [[Benchmark]] (M3) can be rerun. Groq's free plan, for example, allows 1,000 requests and 200K tokens per day per model, and only 8K tokens per minute, so one large-diff prompt can exceed the per-minute cap on its own.

**Consequences**
1. **The [[Eval Harness]] response cache is load-bearing**, not a cost optimisation. Keyed by model + prompt hash, an unchanged case must never re-call any provider.
2. **The first full 150–300 case benchmark run may need batching across multiple days.**
3. **Provider availability is volatile.** The cascade must degrade gracefully when a provider disappears entirely, not just when it rate-limits. During model selection `gemini-2.5-flash` was still listed but returned 404.

**Mitigation**
- Four-provider cascade with any-error fallback ([[ADR-021 Free-tier four-provider LLM cascade]])
- Cache every eval call ([[Eval Harness]])
- Fixed 50-case dev subset per PR in the [[CI Quality Gate]]; full dev split nightly, which may itself need to fit within daily caps

**Affects:** [[Benchmark]], [[Eval Harness]], [[CI Quality Gate]], [[LLM Client]]
