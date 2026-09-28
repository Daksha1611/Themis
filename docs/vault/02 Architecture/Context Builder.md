---
type: component
status: planned
tags: [component]
related:
  - "[[Job Queue]]"
  - "[[Review Graph]]"
  - "[[tree-sitter]]"
  - "[[Qdrant]]"
  - "[[ADR-004 Qdrant hybrid search]]"
  - "[[ADR-001 Python-only v1]]"
---

# Context Builder

**Purpose:** give the reviewer the PR diff plus the related code from the rest of the repo.

**Responsibilities**
- Fetch the PR diff
- Maintain a repo index: code chunked by function with [[tree-sitter]], stored in [[Qdrant]]
- Query the index with hybrid search (BM25 + embeddings) to retrieve related code

**Inputs:** a review job from the [[Job Queue]] (PR identity); the repository's code.
**Outputs:** the diff and retrieved related code, passed to the [[Review Graph]]. The exact output format is not yet specified.

**Planned code location:** `app/context/` (tree-sitter chunking, Qdrant hybrid retrieval); diff fetch in `app/github/`.

**Dependencies:** [[tree-sitter]], [[Qdrant]]. Decisions: [[ADR-004 Qdrant hybrid search]], [[ADR-001 Python-only v1]].
