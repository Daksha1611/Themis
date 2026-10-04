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

## Measured: dev dry run (2026-10-03)
`python -m evals.runner --split dev --dry-run`, 121 scored cases, pinned `groq` / `openai/gpt-oss-120b` ([[ADR-024 Eval runs pin a single provider and model]]). Token estimates use tiktoken `cl100k_base`, not the model's own tokenizer.
- Prompts: max 1,703 tokens, total 125,635, which is **63% of Groq's 200K tokens/day**.
- Largest request (prompt + `max_tokens` 2,048): 3,751, under the 8K/minute ceiling, so every case fits.
- **Completions decide the day.** The run fits one day only if responses average at most 615 completion tokens. With every response at full `max_tokens`, the total would be 373,443 (187%).
- Eight earlier production `gpt-oss-120b` generations (Langfuse, read-only) averaged **822 completion tokens** (range 93–1,257). That puts the expected total near 225K, so the dev run most likely spans **two days** via `--resume`.

## Measured: dev baseline run (2026-10-03)
- The whole dev run (121 cases) finished in **one session**: about 1 hour (12:23–13:23 UTC), 122 provider calls (one per-minute retry).
- Tokens: 219,611 in all (132,719 prompt, 86,892 completion; mean 718 completion tokens per case).
- **No daily-limit (TPD) response arrived**, although the total exceeds the 200K tokens/day taken from Groq's docs on 2026-10-01. Either the documented daily limit does not apply as recorded, or it is counted differently. Re-verify before relying on it ([[09 External Facts]]).
- Pacing by an estimated prompt + `max_tokens` per request kept the run under 8K tokens/minute; one per-minute 429 was retried.
- Actual prompt tokens ran 5.6% above the `cl100k_base` estimate (132,719 vs 125,635).

**Affects:** [[Benchmark]], [[Eval Harness]], [[CI Quality Gate]], [[LLM Client]]
