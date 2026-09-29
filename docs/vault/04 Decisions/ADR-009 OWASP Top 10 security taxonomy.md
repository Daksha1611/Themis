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

## Open Reconsideration
**Status unchanged (accepted). Decision needed from the project owner before building the security pass node** ([[Open Questions]], Q37b). Neither taxonomy is implemented yet.

- OWASP Top 10 (2021) was initially chosen. A 2025 edition exists.
- Themis reviews general Python code rather than web apps specifically, so **CWE Top 25** (Common Weakness Enumeration) may map better to code-level bugs.
- CWE categories cited in favour: CWE-476 (null dereference), CWE-125 (out-of-bounds read), CWE-416 (use-after-free analogues in Python), CWE-362 (race condition), as more directly tied to Python logic bugs than web-app-centric OWASP categories.
- **Fact check to weigh before deciding:**
  - CWE-125 and CWE-416 are memory-safety weaknesses. Pure Python is memory-safe, so they mainly apply to C extensions.
  - CWE-476 and CWE-362 overlap with the logic-bug categories `null-or-none-handling` and `concurrency-or-async` ([[ADR-019 Logic bug taxonomy]]), so they may count as logic bugs, not security findings.
- The rejection in "Alternatives considered" concerns the full CWE list; CWE Top 25 has only 25 entries.
