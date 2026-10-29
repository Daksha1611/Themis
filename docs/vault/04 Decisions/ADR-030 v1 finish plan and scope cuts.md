---
name: ADR-030 v1 finish plan and scope cuts
description: "Decision: v1 finishes in three weeks (M4 runs in the background, M5 from cached findings, then M6, M7, deployment and the holdout); the probe, the security benchmark track and large-PR handling are cut from v1."
type: decision
status: accepted
tags: [decision]
related:
  - "[[Roadmap]]"
  - "[[Current Status]]"
  - "[[ADR-029 Aggregated evaluation]]"
  - "[[ADR-014 Incremental repo indexing]]"
  - "[[ADR-008 Encoder classifier as precision filter]]"
  - "[[CI Quality Gate]]"
  - "[[Open Questions]]"
---

# ADR-030 v1 finish plan and scope cuts

Owner decision, 2026-10-28.

## Context
- **The quota sets the pace.** Each M4 run costs 1.3–2.1 days of Groq's free quota, and [[ADR-029 Aggregated evaluation]] asks for three runs per configuration, so the M4 comparison alone takes about 9 days.
- **Other work does not need the quota.** M5 can be built from the findings already cached by the dev runs. M6 and M7 need no new eval runs.

## Decision
**Three-week plan** (detail in [[Roadmap]]):
- **Week 1:** wire M4 behind a flag; start the M4 runs in the background; build M5 from cached findings.
- **Week 2:** the M4 result; M6 (guardrails plus the injection set); M7 (an eval gate based on the run fingerprint); deployment.
- **Week 3:** label the holdout; the final holdout runs; publish the results page; the demo.

**Scope cuts and settings:**
- **The reshaped probe is cancelled.** Eval and production stay on the model's default (medium) reasoning effort. v2 counts as run 1 of the baseline arm. The probe's partial data (6 calls, 1 case) is kept but not used for any decision.
- **The security benchmark track (Q58) is deferred to post-v1.** Security recall stays reported as not statistically meaningful.
- **Q48 (large PRs) becomes a documented limitation** in the README; it is not built in v1.
- **The M7 gate makes no LLM calls in CI.** Details are decided in week 2.

**M4 wiring (week 1):**
- **`CONTEXT_BUDGET`** setting: 0 turns context off and is the production default until the M4 result says otherwise.
- **Equivalence rule:** with the budget at 0, the rendered prompts must hash to v2's recorded prompt hash. New baseline-arm runs are then pooled with v2, even though the code hash changed.
- **Production index lifecycle (amends [[ADR-014 Incremental repo indexing]]):**
  - The context is built per review from a snapshot of the PR head.
  - Blob sources, chunks and embeddings are cached by content hash, so each PR fetches and embeds only blobs not seen before. This is the incremental behaviour ADR-014 asks for.
  - The first review of a repository builds the cache: the "on install" index happens lazily.
  - `python -m app.context.reindex <owner/repo>` warms the cache for the default branch: the manual command.
  - No persistent Qdrant service: a per-review in-memory collection over cached vectors.

**M5 (week 1, from cached findings):**
- **Labels are automatic and location-based,** replacing manual labelling for v1. A finding is real if it lands on a strict bug-holding range of a buggy case; it is noise if it is on a clean case or off-range on a buggy case.
- **The comparison:** a feature-based reference model and the [[ADR-008 Encoder classifier as precision filter|encoder]]; whichever cross-validates better is kept.
- **Dependencies:** `scikit-learn` and `transformers` become declared dependencies (a `filter` extra), along with `pyyaml` (the run plans). All three were already installed as transitive dependencies of `sentence-transformers`, at the same versions.

## Alternatives considered
- **Finish the probe first:** it needs another quota day and could only lower the per-run cost.
- **A persistent Qdrant index fed by install webhooks** (ADR-014 as written).

## Consequences
- **The M4 result arrives in week 2,** about 9 days after the runs start.
- **Location-based labels** count a correct finding on an unlabelled issue as noise, so the filter learns some "correct but unlabelled" findings as noise. This is stated in the M5 report.
- **Production context** costs one tree listing per review plus fetches of new blobs; the first review of a large repository is slow.
