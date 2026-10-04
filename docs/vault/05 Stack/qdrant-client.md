---
name: qdrant-client
description: "qdrant-client: Python client for Qdrant; its in-memory mode serves the tests and the retrieval eval."
type: tech
status: in-progress
tags: [tech]
related:
  - "[[Qdrant]]"
  - "[[Context Builder]]"
version: 1.19.1 (pinned in the context extra; matches the local Qdrant server 1.19.1; read via importlib.metadata 2026-10-04)
---

# qdrant-client

The Python client for [[Qdrant]], used by `app/context/index.py`.

**Checked against the installed version:** hybrid search through `query_points()`, with one `Prefetch` per named vector (dense and sparse) and `FusionQuery(fusion=Fusion.RRF)`. Sparse vectors use `SparseVectorParams(modifier=Modifier.IDF)`, so Qdrant supplies the inverse document frequency.

**In-memory mode** (`QdrantClient(":memory:")`) supports both features. Tests and the retrieval eval use it, never the running service's collections.
