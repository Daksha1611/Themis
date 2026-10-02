---
name: Eval Cost
description: "Risk that benchmark and CI eval runs exhaust the daily request and token budget of the free-tier LLM providers."
type: risk
status: in-progress
tags: [risk]
related:
  - "[[Eval Harness]]"
  - "[[CI Quality Gate]]"
  - "[[Drift Monitoring]]"
  - "[[LLM Client]]"
  - "[[Benchmark]]"
  - "[[Free Tier Throughput]]"
  - "[[ADR-021 Free-tier four-provider LLM cascade]]"
---

# Eval Cost

**Risk:** every eval run spends **request budget**. Themis runs on free tiers only ([[ADR-021 Free-tier four-provider LLM cascade]]), so actual spend is $0; the binding constraint is **requests and tokens per day (and per minute) per provider**, not dollars. A benchmark of 150–300 cases, rerun during tuning, can exhaust a provider's daily budget (Groq: 1,000 requests and 200K tokens per day, 8K tokens per minute; see [[09 External Facts]]).

This risk and [[Free Tier Throughput]] are two views of the same constraint: this note covers *eval* runs consuming the budget; Free Tier Throughput covers what the caps do to how often the benchmark can be rerun.

**Mitigation** (shared with [[Free Tier Throughput]]; one set of measures serves both)
- **Response cache** keyed by model + prompt hash: an unchanged case never re-calls any provider ([[Eval Harness]]). Planned (M3 Step 4); load-bearing, not an optimisation
- **Dev-split-only CI runs:** a fixed 50-case dev subset per PR, the full dev split nightly; holdout only at milestones ([[CI Quality Gate]], [[ADR-007 dev-holdout benchmark split]])
- **Batched first run:** the first full benchmark run may be spread across several days to stay within daily caps
- **Four-provider cascade:** when one provider's budget is spent, the next answers ([[ADR-021 Free-tier four-provider LLM cascade]]). In place

`cost_usd` remains a list-price estimate for reporting cost per PR ([[Metrics]]); it is not money spent.

**Affects:** [[Eval Harness]], [[CI Quality Gate]], [[Drift Monitoring]], [[LLM Client]], [[Benchmark]]
