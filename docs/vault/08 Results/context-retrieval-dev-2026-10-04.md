---
name: context-retrieval-dev-2026-10-04
description: "Symbol-definition recall of the M4 context builder on the dev split at several token budgets, with the leakage check; no LLM calls."
type: reliability
status: done
tags: [reliability, results]
related:
  - "[[ADR-027 Eval-time repo context]]"
  - "[[Context Builder]]"
  - "[[Eval Harness]]"
---

> **Superseded by [[context-retrieval-dev-2026-10-05]]** (structural lookup, [[ADR-028 Structural lookup plus hybrid search]]). Kept as written: the pure-hybrid result that motivated ADR-028.

# Context retrieval: dev split

Retrieval quality of the M4 context builder ([[ADR-027 Eval-time repo context]], [[Context Builder]]), measured with **no LLM calls**. Not wired into the review path.

- Generated 2026-10-04T15:37:24+00:00 by `python -m evals.context_eval --split dev` at git `f8dd95e`; embedder `sentence-transformers/all-MiniLM-L6-v2`; in-memory Qdrant
- Cases: 121 scored dev cases; 64 have at least one target; 156 targets in all
- **Symbol-definition recall:** of the functions, methods and classes referenced in a diff's changed lines that are defined in the package snapshot outside the diff itself, the share whose definition is retrieved within the token budget. Pooled over (case, name) pairs; 95% Wilson intervals.

## Overall

| Group | 1000 tokens | 2000 tokens | 4000 tokens |
|---|---|---|---|
| All cases | 21.2% (33/156; 15.5%–28.2%) | 23.7% (37/156; 17.7%–31.0%) | 25.0% (39/156; 18.9%–32.3%) |

## By repo

| Group | 1000 tokens | 2000 tokens | 4000 tokens |
|---|---|---|---|
| Textualize/rich | 7.3% (3/41; 2.5%–19.4%) | 9.8% (4/41; 3.9%–22.5%) | 9.8% (4/41; 3.9%–22.5%) |
| agronholm/anyio | 26.9% (18/67; 17.7%–38.5%) | 29.9% (20/67; 20.2%–41.7%) | 29.9% (20/67; 20.2%–41.7%) |
| fastapi/fastapi | 12.5% (3/24; 4.3%–31.0%) | 12.5% (3/24; 4.3%–31.0%) | 12.5% (3/24; 4.3%–31.0%) |
| marshmallow-code/marshmallow | 50.0% (2/4; 15.0%–85.0%) | 50.0% (2/4; 15.0%–85.0%) | 50.0% (2/4; 15.0%–85.0%) |
| pallets/click | 35.0% (7/20; 18.1%–56.7%) | 40.0% (8/20; 21.9%–61.3%) | 50.0% (10/20; 29.9%–70.1%) |

## By category

| Group | 1000 tokens | 2000 tokens | 4000 tokens |
|---|---|---|---|
| CWE-20 | n/a | n/a | n/a |
| CWE-400 | 0.0% (0/2; 0.0%–65.8%) | 0.0% (0/2; 0.0%–65.8%) | 0.0% (0/2; 0.0%–65.8%) |
| arithmetic-or-numeric | 0.0% (0/2; 0.0%–65.8%) | 0.0% (0/2; 0.0%–65.8%) | 0.0% (0/2; 0.0%–65.8%) |
| clean | 16.7% (9/54; 9.0%–28.7%) | 18.5% (10/54; 10.4%–30.8%) | 18.5% (10/54; 10.4%–30.8%) |
| concurrency-or-async | 19.0% (4/21; 7.7%–40.0%) | 33.3% (7/21; 17.2%–54.6%) | 28.6% (6/21; 13.8%–50.0%) |
| control-flow | 14.3% (3/21; 5.0%–34.6%) | 19.0% (4/21; 7.7%–40.0%) | 19.0% (4/21; 7.7%–40.0%) |
| error-handling | 25.0% (3/12; 8.9%–53.2%) | 25.0% (3/12; 8.9%–53.2%) | 25.0% (3/12; 8.9%–53.2%) |
| null-or-none-handling | 60.0% (3/5; 23.1%–88.2%) | 60.0% (3/5; 23.1%–88.2%) | 60.0% (3/5; 23.1%–88.2%) |
| off-by-one-or-boundary | 0.0% (0/2; 0.0%–65.8%) | 0.0% (0/2; 0.0%–65.8%) | 0.0% (0/2; 0.0%–65.8%) |
| resource-leak | 28.6% (2/7; 8.2%–64.1%) | 28.6% (2/7; 8.2%–64.1%) | 28.6% (2/7; 8.2%–64.1%) |
| type-or-contract | 30.0% (9/30; 16.7%–47.9%) | 26.7% (8/30; 14.2%–44.4%) | 36.7% (11/30; 21.9%–54.5%) |

## Leakage check

- Chunks retrieved from test, doc, changelog or CI paths, across all cases and budgets: **0**
- Files indexed from such paths: **0**
- Package paths skipped by the exclusion rule: none

## Indexing

- Mean 2.6 s per case snapshot (max 45.0 s), mean 718 chunks
- Embedding cache: 82964 hits, 4699 misses (hit rate 94.6%); total wall time 368 s

## Caveats

- Symbol-definition recall measures retrieval only, not whether the context helps the review. That is the next ablation row, after baseline v2.
- A referenced name counts as retrieved if any definition with that name is retrieved; names defined several times can match a different definition.
- Dense embeddings truncate chunks at 256 tokens; sparse vectors cover the whole chunk.
