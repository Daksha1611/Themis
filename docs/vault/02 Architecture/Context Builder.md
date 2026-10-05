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

**In progress (M4 groundwork, 2026-10-04):** standalone in `app/context/`, **not wired into the review path**. Eval-time snapshots: [[ADR-027 Eval-time repo context]]. First retrieval measurement: [[context-retrieval-dev-2026-10-04]]. Symbol-definition recall is 21–25% at 1K–4K tokens, with no leakage.

**Code location:** `app/context/`.

**Dependencies:** [[tree-sitter]] with [[tree-sitter-python]], [[Qdrant]] via [[qdrant-client]], [[sentence-transformers]] on [[torch]] (CPU), [[GitHub Integration]]. Decisions: [[ADR-004 Qdrant hybrid search]], [[ADR-014 Incremental repo indexing]], [[ADR-015 Local embeddings and Qdrant native hybrid search]], [[ADR-001 Python-only v1]].
