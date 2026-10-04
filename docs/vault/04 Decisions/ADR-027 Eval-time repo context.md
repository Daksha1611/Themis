---
name: ADR-027 Eval-time repo context
description: "Decision: benchmark cases get repo context from the fix commit's tree, package source only (no tests, docs, changelog or CI); embeddings are cached by content hash; production indexing stays as ADR-014."
type: decision
status: accepted
tags: [decision]
related:
  - "[[Context Builder]]"
  - "[[ADR-014 Incremental repo indexing]]"
  - "[[ADR-015 Local embeddings and Qdrant native hybrid search]]"
  - "[[Benchmark]]"
  - "[[Benchmark Leakage]]"
  - "[[Eval Harness]]"
---

# ADR-027 Eval-time repo context

Owner decision, 2026-10-04 (M4 groundwork).

## Context
M4 adds repo context to the review: related code retrieved from the rest of the repository ([[Context Builder]]). The production rule is set by [[ADR-014 Incremental repo indexing]]: a full index on install, then incremental updates per PR.

Benchmark cases are not live PRs. Each is a synthetic PR that reverts a bug fix, so the eval must decide which repository state the context comes from, and must not leak the answer through retrieval.

## Decision
- **Snapshot rule.** A benchmark case's context is built from the repository tree at the case's **fix commit**: the base the synthetic PR applies to. **Package source only:** the package directory used for case construction (for example `src/click/`). No tests, docs, changelog or CI files.
  - *Why:* fix commits often add a regression test named after the bug, and changelogs describe the fix. Indexing either would leak the answer through retrieval. This is the same principle as the revert-scope rule (Q56: package source only).
  - The base tree contains the pre-PR (fixed) version of the changed functions. That is what a real PR's base shows, and the diff's removed and context lines already show it.
- **Retrieved chunks exclude the diff's own changed regions.** A chunk overlapping a changed line of the same file adds nothing the diff does not already show.
- **Production rule unchanged:** a full index of the default branch on install, then incremental per PR (Q12, [[ADR-014 Incremental repo indexing]]).
- **Embedding cache.** Chunks are embedded once and cached by SHA-256 of (model, chunk text). Benchmark cases share repos across many commits, and most chunks are unchanged between them, so they are reused instead of re-embedded. The eval cache lives in `evals/.cache/` (git-ignored).
- **Hybrid search per [[ADR-015 Local embeddings and Qdrant native hybrid search]]:**
  - dense: `all-MiniLM-L6-v2` (sentence-transformers, CPU-only torch);
  - sparse: code-aware term counts, with identifiers split into their `snake_case` and `camelCase` parts, and IDF applied by Qdrant's sparse-vector modifier, so there is no separate BM25 index and no extra dependency;
  - fusion: Reciprocal Rank Fusion.

  Retrieval is purely hybrid, with no exact symbol lookup, so retrieval quality is measured rather than built into the metric.
- **Measured before it is wired in.** Symbol-definition recall (`evals/context_eval.py`) is computed with no LLM calls. Context enters the review path only as its own ablation row, after baseline v2.

## Consequences
- Each case needs an index of its own fix-commit snapshot. The embedding cache makes that cheap after the first commit per repo.
- The production index and the eval snapshots share the chunker, embedder and retriever. Only what is indexed differs.
