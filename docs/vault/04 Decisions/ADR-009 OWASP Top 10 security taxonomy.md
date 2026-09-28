---
type: decision
status: done
tags: [decision]
related:
  - "[[Finding Schema]]"
  - "[[Review Graph]]"
  - "[[Benchmark]]"
  - "[[Metrics]]"
  - "[[Prior Art]]"
---


# ADR-009 OWASP Top 10 security taxonomy

**Status:** accepted

## Context
Security findings need a shared vocabulary so they can be labeled in the [[Benchmark]], compared across runs, and reported per category. Proposed from [[Prior Art]].

## Decision
Every security finding carries an OWASP Top 10 category. The [[Review Graph]] security pass assigns it; the [[Finding Schema]] stores it.

## Alternatives considered
- CWE IDs: hundreds of entries, too fine-grained to label or measure on a 150–300-case benchmark.

## Consequences
- The [[Finding Schema]] gains a security category field (exact shape decided when the schema is written).
- Security cases in the [[Benchmark]] are labeled with their OWASP category.
- The OWASP Top 10 edition must be pinned (see [[Open Questions]]).
