---
name: ADR-028 Structural lookup plus hybrid search
description: "Decision: context retrieval fills its token budget with definitions of names the diff references, then callers of functions the diff changes, then hybrid semantic search."
type: decision
status: accepted
tags: [decision]
related:
  - "[[ADR-015 Local embeddings and Qdrant native hybrid search]]"
  - "[[ADR-027 Eval-time repo context]]"
  - "[[Context Builder]]"
  - "[[Eval Harness]]"
---

# ADR-028 Structural lookup plus hybrid search

Owner decision, 2026-10-04. Amends [[ADR-015 Local embeddings and Qdrant native hybrid search]].

## Context
Pure hybrid search (ADR-015) on a diff's changed lines retrieved only 21–25% of the definitions the diff references, at 1K–4K tokens ([[context-retrieval-dev-2026-10-04]]). Recall barely grew with the budget: the ranking, not the budget, was the limit. Similarity search finds neighbouring, similar code; it does not follow references.

## Decision
Retrieval fills the token budget in this priority order:
1. **Definitions of names referenced in the changed lines,** resolved with tree-sitter and import analysis:
   - same-module definitions;
   - imported names (including aliases and relative imports, and `module.name` through an imported module);
   - `self.method` / `cls.method` within the enclosing class.

   Where resolution is ambiguous, the candidates are included and marked `ambiguous`.
2. **Callers of functions the diff changes:** call sites elsewhere in the package of any function or method whose body the diff modifies. Contract bugs break callers.
3. **Hybrid semantic search** (the ADR-015 design) fills whatever budget remains.

Each `RelatedChunk` records its `source` (`definition`, `caller`, `semantic`) and, for structural chunks, the name that led to it (`via`). Chunks overlapping the diff's own changed region stay excluded ([[ADR-027 Eval-time repo context]]).

## Consequences
- **Symbol-definition recall becomes a resolution-coverage check.** It no longer shows that context is useful; that is measured only by the M4 ablation (v2 vs v2 + context, McNemar, with the falsification split).
- Structural lookup needs every snapshot file parsed; the parse is cached per file blob.
