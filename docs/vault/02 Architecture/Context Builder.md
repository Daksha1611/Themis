---
name: Context Builder
description: "Gives the reviewer the diff plus related repo code, using tree-sitter chunks and Qdrant hybrid search."
type: component
status: in-progress
tags: [component]
related:
  - "[[Job Queue]]"
  - "[[Review Graph]]"
  - "[[GitHub Integration]]"
  - "[[Guardrails]]"
  - "[[Finding Schema]]"
  - "[[tree-sitter]]"
  - "[[Qdrant]]"
  - "[[sentence-transformers]]"
  - "[[ADR-004 Qdrant hybrid search]]"
  - "[[ADR-014 Incremental repo indexing]]"
  - "[[ADR-015 Local embeddings and Qdrant native hybrid search]]"
  - "[[ADR-001 Python-only v1]]"
---

# Context Builder

**Purpose:** give the reviewer the PR diff plus the related code from the rest of the repo.

**Responsibilities**
- Get the PR diff from [[GitHub Integration]]
- Maintain a repo index: code chunked by function with [[tree-sitter]], stored in [[Qdrant]]
- Retrieve related code in priority order ([[ADR-028 Structural lookup plus hybrid search]]): definitions of names the diff references (tree-sitter plus import analysis), then callers of functions the diff changes, then hybrid search for the remaining budget. Hybrid search uses dense embeddings from a local [[sentence-transformers]] model (`all-MiniLM-L6-v2` to start) plus Qdrant native sparse vectors, fused with Reciprocal Rank Fusion. No separate BM25 index.

**Index lifecycle** ([[ADR-014 Incremental repo indexing]])
- On install: full index of the default branch
- Per PR: incremental re-index of changed files plus their direct importers only
- Manual: a re-index command for when the index drifts

**Inputs:** a review job from the [[Job Queue]] (PR identity); the repository's code.
**Outputs:** a Pydantic `ReviewContext` ([[Finding Schema]]):
- `pr_metadata`
- `changed_files`: path, hunks, full file content when small
- `related_chunks`: path, symbol name, code, retrieval score, reason retrieved
- `token_budget_used`

The `ReviewContext` is sanitized by [[Guardrails]] before it reaches the [[Review Graph]].

**Index lifecycle as built** ([[ADR-030 v1 finish plan and scope cuts]], amending ADR-014): the context is built per review from the base commit's package source. Blob sources and embeddings are cached by content hash (`CONTEXT_CACHE_DIR`), so a PR fetches and embeds only blobs not seen before. The first review of a repository fills the cache, and `python -m app.context.reindex <owner/repo> --installation-id N` warms it for the default branch. Each review uses an in-memory Qdrant collection; there is no Qdrant service. A package of more than 2,000 files gets no context.

**Wired behind `CONTEXT_BUDGET`** (ADR-030, 2026-10-29):
- **0 = off,** the production default until the M4 result. With context off, the worker never imports `app/context/`, and the prompt is byte-identical to baseline v2's.
- **Above 0:** the worker builds a `ReviewContext` (`related_chunks`, `token_budget`, `token_budget_used`). The prompt gains a `<context>` block after the diff, declared to be data, not instructions; findings go only on diff lines.
- **Failures:** a context build failure is logged and the review proceeds on the diff alone.
- **Not yet populated:** `pr_metadata` and `changed_files` of the spec's `ReviewContext` (the diff already carries both).

**Eval:** per-case snapshots at the fix commit ([[ADR-027 Eval-time repo context]]), frozen per run. Retrieval measurements: pure hybrid [[context-retrieval-dev-2026-10-04]] (symbol-definition recall 21–25%); with structural lookup [[context-retrieval-dev-2026-10-05]] (resolution coverage 57–64%, caller coverage 39–73%, no leakage).

**Code location:** `app/context/` (`builder.py` and `reindex.py` for production), `app/github/contents.py`.

**Dependencies:** [[tree-sitter]] with [[tree-sitter-python]], [[Qdrant]] via [[qdrant-client]], [[sentence-transformers]] on [[torch]] (CPU), [[GitHub Integration]]. Decisions: [[ADR-004 Qdrant hybrid search]], [[ADR-014 Incremental repo indexing]], [[ADR-015 Local embeddings and Qdrant native hybrid search]], [[ADR-001 Python-only v1]].
