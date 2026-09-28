---
type: decision
status: done
tags: [decision]
related:
  - "[[Context Builder]]"
  - "[[Qdrant]]"
  - "[[tree-sitter]]"
---

# ADR-004 Qdrant hybrid search

**Status:** accepted

## Context
Reviewing a diff well requires related code from the rest of the repo.

## Decision
The repo index uses [[tree-sitter]] to chunk code by function, stored in [[Qdrant]], queried with hybrid search (BM25 + embeddings).

## Alternatives considered
- None stated in the spec.

## Consequences
- Qdrant is a required runtime service (in `infra/` docker-compose).
- The contribution of repo context is measured as the "+ repo context" row of the [[Ablation Table]].
