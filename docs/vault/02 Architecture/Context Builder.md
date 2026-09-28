---
type: component
status: planned
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
- Retrieve related code with hybrid search: dense embeddings from a local [[sentence-transformers]] model (`all-MiniLM-L6-v2` to start) plus Qdrant native sparse vectors, fused with Reciprocal Rank Fusion. No separate BM25 index.

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

**Planned code location:** `app/context/`.

**Dependencies:** [[tree-sitter]], [[Qdrant]], [[sentence-transformers]], [[GitHub Integration]]. Decisions: [[ADR-004 Qdrant hybrid search]], [[ADR-014 Incremental repo indexing]], [[ADR-015 Local embeddings and Qdrant native hybrid search]], [[ADR-001 Python-only v1]].
