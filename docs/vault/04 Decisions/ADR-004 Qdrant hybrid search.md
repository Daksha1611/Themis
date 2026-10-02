---
name: ADR-004 Qdrant hybrid search
description: "Decision: a repo index of tree-sitter function chunks in Qdrant with hybrid search; refined by ADR-015."
type: decision
status: accepted
tags: [decision]
related:
  - "[[Context Builder]]"
  - "[[Qdrant]]"
  - "[[tree-sitter]]"
  - "[[ADR-015 Local embeddings and Qdrant native hybrid search]]"
---

# ADR-004 Qdrant hybrid search

> **Refined by [[ADR-015 Local embeddings and Qdrant native hybrid search]] (Q13).** "BM25" below is implemented as Qdrant's native sparse vectors fused with dense embeddings by Reciprocal Rank Fusion. There is no separate BM25 index.

## Context
Reviewing a diff well requires related code from the rest of the repo.

## Decision
The repo index uses [[tree-sitter]] to chunk code by function, stored in [[Qdrant]], queried with hybrid search (BM25 + embeddings).

## Alternatives considered
- None stated in the spec.

## Consequences
- Qdrant is a required runtime service (in `infra/` docker-compose).
- The contribution of repo context is measured as the "+ repo context" row of the [[Ablation Table]].
