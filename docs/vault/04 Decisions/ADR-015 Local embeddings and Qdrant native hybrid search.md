---
type: decision
status: accepted
tags: [decision]
related:
  - "[[Context Builder]]"
  - "[[sentence-transformers]]"
  - "[[Qdrant]]"
  - "[[ADR-004 Qdrant hybrid search]]"
---

# ADR-015 Local embeddings and Qdrant native hybrid search

## Context
[[ADR-004 Qdrant hybrid search]] chose hybrid search (BM25 + embeddings) without saying where embeddings come from or how BM25 is implemented.

## Decision
- **Embeddings:** a local [[sentence-transformers]] model, `all-MiniLM-L6-v2` to start. A code-specific model only if retrieval quality requires it.
- **Hybrid search:** [[Qdrant]]'s native sparse vector support with Reciprocal Rank Fusion (RRF).
- No separate BM25 index.

## Alternatives considered
- Embedding API: embedding a whole repo via API is slow and expensive.
- Separate BM25 index: unnecessary, since Qdrant supports sparse vectors natively.

## Consequences
- sentence-transformers joins the tech stack.
- Embeddings are computed on Themis's own host.
- Changing the embedding model requires re-indexing.
- How sparse vectors are produced must be checked against the installed Qdrant version before use.
