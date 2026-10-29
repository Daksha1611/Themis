---
name: ADR-014 Incremental repo indexing
description: "Decision: index the repo on install, incrementally per PR, and manually on demand."
type: decision
status: accepted
tags: [decision]
related:
  - "[[Context Builder]]"
  - "[[Qdrant]]"
  - "[[tree-sitter]]"
---

# ADR-014 Incremental repo indexing

> **Amended by [[ADR-030 v1 finish plan and scope cuts]] (2026-10-28):** in v1 the index is built per review from content-addressed caches (blob sources, chunks, embeddings). Only blobs not seen before are fetched and embedded; the first review of a repository builds the cache; `python -m app.context.reindex` warms it. There is no persistent Qdrant service.

## Context
The [[Context Builder]] needs a current repo index. Full indexing on every PR is far too slow for a webhook flow.

## Decision
- **On install:** full index of the default branch.
- **Per PR:** incremental re-index of changed files plus their direct importers only.
- **Manual:** a re-index command for when the index drifts.

## Alternatives considered
- Full index on every PR: far too slow for a webhook flow.

## Consequences
- The index can drift from the repo; the manual re-index command covers this.
- Finding a changed file's direct importers requires knowing the repo's import relationships.
