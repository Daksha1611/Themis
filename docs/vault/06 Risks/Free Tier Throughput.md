---
name: Free Tier Throughput
description: "Risk that free-tier rate limits bound how often the benchmark can run."
type: risk
status: in-progress
tags: [risk]
related:
  - "[[Benchmark]]"
  - "[[Eval Harness]]"
  - "[[CI Quality Gate]]"
  - "[[ADR-021 Free-tier four-provider LLM cascade]]"
  - "[[LLM Client]]"
  - "[[Eval Cost]]"
---

# Free Tier Throughput

**Risk:** free-tier daily request caps constrain how often the [[Benchmark]] (M3) can be rerun. Groq's free plan, for example, allows 1,000 requests and 200K tokens per day per model, and only 8K tokens per minute, so one large-diff prompt can exceed the per-minute cap on its own.

**Consequences**
1. **The [[Eval Harness]] response cache is load-bearing**, not a cost optimisation. Keyed by model + prompt hash, an unchanged case must never re-call any provider.
2. **The first full 150–300 case benchmark run may need batching across multiple days.**
3. **Provider availability is volatile.** The cascade must degrade gracefully when a provider disappears entirely, not just when it rate-limits. During model selection `gemini-2.5-flash` was still listed but returned 404.

**Mitigation** (shared with [[Eval Cost]]; one set of measures serves both)
- **Response cache** keyed by model + prompt hash: an unchanged case never re-calls any provider ([[Eval Harness]]). Planned (M3 Step 4); load-bearing, not an optimisation
- **Dev-split-only CI runs:** a fixed 50-case dev subset per PR, the full dev split nightly; holdout only at milestones ([[CI Quality Gate]], [[ADR-007 dev-holdout benchmark split]])
- **Batched first run:** the first full benchmark run may be spread across several days to stay within daily caps
- **Four-provider cascade:** when one provider's budget is spent, the next answers ([[ADR-021 Free-tier four-provider LLM cascade]]). In place

**Affects:** [[Benchmark]], [[Eval Harness]], [[CI Quality Gate]], [[LLM Client]]
