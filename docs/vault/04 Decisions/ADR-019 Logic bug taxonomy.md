---
name: ADR-019 Logic bug taxonomy
description: "Decision: the seven logic-bug categories a finding may use."
type: decision
status: accepted
tags: [decision]
related:
  - "[[Finding Schema]]"
  - "[[Review Graph]]"
  - "[[Benchmark]]"
  - "[[Metrics]]"
  - "[[ADR-022 CWE Top 25 security taxonomy]]"
  - "[[ADR-023 Arithmetic-or-numeric logic category]]"
---

# ADR-019 Logic bug taxonomy

> **Amended by [[ADR-023 Arithmetic-or-numeric logic category]] (2026-10-02):** adds `arithmetic-or-numeric` and precedence rules for overlapping categories. The seven categories below stand.

## Context
Without a taxonomy for logic bugs, the metrics cannot show what the reviewer is weak at.

## Decision
Logic-bug findings use one of these categories:
- `null-or-none-handling`
- `off-by-one-or-boundary`
- `error-handling`
- `concurrency-or-async`
- `resource-leak`
- `type-or-contract`
- `control-flow`

Per-category recall becomes a reportable table.

## Alternatives considered
- A single "logic bug" category: cannot show what the reviewer is weak at.

## Consequences
- [[Finding Schema]] `category` values include these seven.
- [[Benchmark]] cases are labeled with a category.
- [[Metrics]] reports per-category recall.
