---
name: context-retrieval-dev-2026-10-05
description: "Resolution coverage, caller coverage and budget composition of the M4 context builder (structural lookup + hybrid) on the dev split, with the leakage check; no LLM calls."
type: reliability
status: done
tags: [reliability, results]
related:
  - "[[ADR-028 Structural lookup plus hybrid search]]"
  - "[[ADR-027 Eval-time repo context]]"
  - "[[Context Builder]]"
  - "[[Eval Harness]]"
---

# Context retrieval: dev split (structural lookup + hybrid)

Retrieval of the M4 context builder with structural lookup ([[ADR-028 Structural lookup plus hybrid search]], [[ADR-027 Eval-time repo context]]), measured with **no LLM calls**. Not wired into the review path.

- Generated 2026-10-05T09:00:47+00:00 by `python -m evals.context_eval --split dev` at git `d5d8d67`; embedder `sentence-transformers/all-MiniLM-L6-v2`; in-memory Qdrant
- Cases: 121 scored dev cases; 64 reference at least one external definition (156 targets in all); 95 change a function that has in-package call sites

> **Symbol-definition recall is now a resolution-coverage check, not evidence of usefulness.** Structural lookup retrieves definitions of referenced names by construction, so a high number shows the resolver and the budget work. Whether context helps the review is measured only by the M4 ablation (v2 vs v2 + context, McNemar, falsification split; [[Eval Harness]]).

## Symbol-definition recall (resolution coverage)

| Group | 1000 tokens | 2000 tokens | 4000 tokens |
|---|---|---|---|
| Pure hybrid (2026-10-04, superseded) | 21.2% (33/156; 15.5%–28.2%) | 23.7% (37/156; 17.7%–31.0%) | 25.0% (39/156; 18.9%–32.3%) |
| **Structural + hybrid** | 57.1% (89/156; 49.2%–64.6%) | 58.3% (91/156; 50.5%–65.8%) | 63.5% (99/156; 55.7%–70.6%) |

By repo (structural + hybrid):

| Group | 1000 tokens | 2000 tokens | 4000 tokens |
|---|---|---|---|
| Textualize/rich | 39.0% (16/41; 25.7%–54.3%) | 43.9% (18/41; 29.9%–59.0%) | 46.3% (19/41; 32.1%–61.3%) |
| agronholm/anyio | 70.1% (47/67; 58.3%–79.8%) | 68.7% (46/67; 56.8%–78.5%) | 70.1% (47/67; 58.3%–79.8%) |
| fastapi/fastapi | 45.8% (11/24; 27.9%–64.9%) | 45.8% (11/24; 27.9%–64.9%) | 62.5% (15/24; 42.7%–78.8%) |
| marshmallow-code/marshmallow | 50.0% (2/4; 15.0%–85.0%) | 50.0% (2/4; 15.0%–85.0%) | 75.0% (3/4; 30.1%–95.4%) |
| pallets/click | 65.0% (13/20; 43.3%–81.9%) | 70.0% (14/20; 48.1%–85.5%) | 75.0% (15/20; 53.1%–88.8%) |

## Remaining misses at 4000 tokens

| Reason | Targets |
|---|---|
| name not bound to a package definition here | 34 |
| attribute on an object of unknown type (too many candidates) | 6 |
| not a resolvable reference (keyword argument, import name or string) | 5 |
| self attribute not a method of the class or its bases | 5 |
| attribute with no method of that name in the package | 3 |
| resolved, but did not fit the budget | 2 |
| attribute of an imported module, not defined there | 1 |
| self/cls outside a class | 1 |

## Caller coverage

For diffs that modify a function: the share of its in-package call sites (matched by the callee's name, outside the diff) whose enclosing function or method is in the context.

| Group | 1000 tokens | 2000 tokens | 4000 tokens |
|---|---|---|---|
| Call sites | 39.1% (368/942; 36.0%–42.2%) | 53.4% (503/942; 50.2%–56.6%) | 72.7% (685/942; 69.8%–75.5%) |

## Budget composition

Average share of the token budget per source (cases with any context):

| Source | 1000 tokens | 2000 tokens | 4000 tokens |
|---|---|---|---|
| definition | 9.3% | 6.1% | 4.8% |
| caller | 39.7% | 34.7% | 25.6% |
| semantic | 48.5% | 57.0% | 66.9% |

## By category (structural + hybrid)

| Group | 1000 tokens | 2000 tokens | 4000 tokens |
|---|---|---|---|
| CWE-20 | n/a | n/a | n/a |
| CWE-400 | 50.0% (1/2; 9.5%–90.5%) | 50.0% (1/2; 9.5%–90.5%) | 50.0% (1/2; 9.5%–90.5%) |
| arithmetic-or-numeric | 0.0% (0/2; 0.0%–65.8%) | 0.0% (0/2; 0.0%–65.8%) | 0.0% (0/2; 0.0%–65.8%) |
| clean | 55.6% (30/54; 42.4%–68.0%) | 59.3% (32/54; 46.0%–71.3%) | 61.1% (33/54; 47.8%–73.0%) |
| concurrency-or-async | 61.9% (13/21; 40.9%–79.2%) | 57.1% (12/21; 36.5%–75.5%) | 61.9% (13/21; 40.9%–79.2%) |
| control-flow | 57.1% (12/21; 36.5%–75.5%) | 57.1% (12/21; 36.5%–75.5%) | 71.4% (15/21; 50.0%–86.2%) |
| error-handling | 66.7% (8/12; 39.1%–86.2%) | 66.7% (8/12; 39.1%–86.2%) | 66.7% (8/12; 39.1%–86.2%) |
| null-or-none-handling | 100.0% (5/5; 56.6%–100.0%) | 100.0% (5/5; 56.6%–100.0%) | 100.0% (5/5; 56.6%–100.0%) |
| off-by-one-or-boundary | 0.0% (0/2; 0.0%–65.8%) | 0.0% (0/2; 0.0%–65.8%) | 0.0% (0/2; 0.0%–65.8%) |
| resource-leak | 85.7% (6/7; 48.7%–97.4%) | 85.7% (6/7; 48.7%–97.4%) | 85.7% (6/7; 48.7%–97.4%) |
| type-or-contract | 46.7% (14/30; 30.2%–63.9%) | 50.0% (15/30; 33.2%–66.8%) | 60.0% (18/30; 42.3%–75.4%) |

## Leakage check

- Chunks retrieved from test, doc, changelog or CI paths, across all cases and budgets: **0**
- Files indexed from such paths: **0**

## Indexing

- Mean 0.8 s per case snapshot (max 1.8 s), mean 718 chunks
- Embedding cache: 87663 hits, 0 misses (hit rate 100.0%); total wall time 203 s

## Caveats

- A referenced name counts as retrieved if any definition with that name is retrieved; names defined several times can match a different definition.
- Call sites are matched by the callee's name, without type information, so a method name shared by several classes yields callers of all of them (marked ambiguous).
- Dense embeddings truncate chunks at 256 tokens; sparse vectors cover the whole chunk.
