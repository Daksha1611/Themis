---
name: sentence-transformers
description: "sentence-transformers: local embeddings for the repo index."
type: tech
status: in-progress
tags: [tech]
related:
  - "[[Context Builder]]"
  - "[[ADR-015 Local embeddings and Qdrant native hybrid search]]"
version: 6.1.0 (pinned in the context extra; read via importlib.metadata 2026-10-04)
---

# sentence-transformers

**What it is:** Python library for computing text embeddings with local models.

**What it does in Themis:** Computes code-chunk embeddings for the repo index (`all-MiniLM-L6-v2` to start).

**Used by:** [[Context Builder]], [[ADR-015 Local embeddings and Qdrant native hybrid search]]

**Version:** not installed yet.
