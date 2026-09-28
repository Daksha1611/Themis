---
type: tech
status: planned
tags: [tech]
related:
  - "[[Context Builder]]"
  - "[[ADR-004 Qdrant hybrid search]]"
version:
---

# Qdrant

**What it is:** Vector database.

**What it does in Themis:** Stores function-level code chunks; serves hybrid retrieval using native sparse vectors plus dense embeddings, fused with Reciprocal Rank Fusion. Qdrant Cloud free tier is an option to shrink the VPS.

**Used by:** [[Context Builder]], [[ADR-004 Qdrant hybrid search]], [[ADR-014 Incremental repo indexing]], [[ADR-015 Local embeddings and Qdrant native hybrid search]], [[ADR-018 Paid VPS over free tier hosting]]

**Version:** not installed yet.
