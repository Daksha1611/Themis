---
type: decision
status: accepted
tags: [decision]
related:
  - "[[Finding Schema]]"
  - "[[Review Graph]]"
  - "[[Benchmark]]"
  - "[[Metrics]]"
  - "[[ADR-009 OWASP Top 10 security taxonomy]]"
---

# ADR-019 Logic bug taxonomy

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
