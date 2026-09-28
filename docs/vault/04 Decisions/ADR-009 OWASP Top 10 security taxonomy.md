---
type: decision
status: accepted
tags: [decision]
related:
  - "[[Finding Schema]]"
  - "[[Review Graph]]"
  - "[[Benchmark]]"
  - "[[Metrics]]"
  - "[[Prior Art]]"
  - "[[ADR-019 Logic bug taxonomy]]"
---


# ADR-009 OWASP Top 10 security taxonomy

## Context
Security findings need a shared vocabulary so they can be labeled in the [[Benchmark]], compared across runs, and reported per category. Proposed from [[Prior Art]].

## Decision
Every security finding carries an OWASP Top 10 category. The [[Review Graph]] security pass assigns it; the [[Finding Schema]] stores it.

## Alternatives considered
- CWE IDs: hundreds of entries, too fine-grained to label or measure on a 150–300-case benchmark.

## Consequences
- The [[Finding Schema]] gains a security category field (exact shape decided when the schema is written).
- Security cases in the [[Benchmark]] are labeled with their OWASP category.
- Pinned edition: **OWASP Top 10 (2021)**. A 2025 edition exists.
- A real security issue that fits no category uses `security-other` with a required free-text subcategory. How often it fires is tracked: frequent use means the taxonomy is wrong.

## Open reconsideration (Q37): awaiting decision
Themis reviews Python code in general, not web apps specifically. **CWE Top 25** may map better to code-level bugs.
- **Option A:** keep OWASP Top 10 (2021).
- **Option B:** switch to CWE Top 25.

The CWE rejection above concerns the full CWE list; CWE Top 25 has only 25 entries. This ADR is unchanged until the decision is made ([[Open Questions]]).
