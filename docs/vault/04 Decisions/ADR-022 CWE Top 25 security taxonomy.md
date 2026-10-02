---
name: ADR-022 CWE Top 25 security taxonomy
description: "Decision: security findings use a Python-reachable CWE Top 25 (2024) entry or security-other."
type: decision
status: accepted
tags: [decision]
related:
  - "[[ADR-009 OWASP Top 10 security taxonomy]]"
  - "[[ADR-019 Logic bug taxonomy]]"
  - "[[Finding Schema]]"
  - "[[Review Graph]]"
  - "[[Benchmark]]"
  - "[[Metrics]]"
---

# ADR-022 CWE Top 25 security taxonomy

Supersedes [[ADR-009 OWASP Top 10 security taxonomy]] (decides Q37 and Q37b).

## Context
Themis reviews general Python code, not web applications specifically. OWASP Top 10 categories describe application-level architectural failures that rarely surface in a single diff. CWE entries map directly to code-visible defects. The [[Benchmark]] also mines fixes from Python libraries whose security commits are described in CWE terms.

## Decision
Security findings use a CWE ID from the **CWE Top 25 (2024 edition)**, restricted to the entries reachable in Python code review. Verified on 2026-10-01 against MITRE's CWE view 1430 (2024 Top 25, CWE version 4.20):

| Category | Weakness |
|---|---|
| `CWE-20` | Improper input validation |
| `CWE-22` | Path traversal |
| `CWE-78` | OS command injection |
| `CWE-79` | Cross-site scripting (HTML generated from Python code) |
| `CWE-89` | SQL injection |
| `CWE-94` | Code injection (`eval`, `exec`, dynamic imports of untrusted input) |
| `CWE-200` | Exposure of sensitive information |
| `CWE-400` | Uncontrolled resource consumption |
| `CWE-502` | Deserialization of untrusted data (`pickle`, unsafe YAML) |
| `CWE-798` | Hard-coded credentials |
| `CWE-918` | Server-side request forgery |
| `security-other` | Any other security issue; **requires a free-text `subcategory`** (carried over from Q39). How often it fires is tracked: frequent use means the taxonomy is wrong. |

The allowed set lives in `app/taxonomy.py`; `Finding` rejects anything else, and the baseline prompt lists every category.

**Edition:** a 2025 edition exists (MITRE CWE view 1435). 2024 is pinned because 2025 drops CWE-798 and CWE-400, two of the weaknesses most visible in a Python diff, and its additions are memory-buffer (CWE-120/121/122) and access-control (CWE-284, 639, 770) entries that are mostly unreachable in Python or overlap CWE-400.

## Alternatives considered
- **OWASP Top 10 (2021):** the superseded ADR-009.
- **Excluded Top 25 entries:**
  - Memory safety (CWE-787, 125, 416, 119, 190, 476): Python is memory-safe; CWE-476 overlaps the logic category `null-or-none-handling`.
  - Authentication and authorisation (CWE-287, 306, 862, 863, 269, 352, 434): application-level, rarely visible in one diff; they fall under `security-other` when they do appear.
  - CWE-77: left to its Python-relevant child CWE-78.
- **Candidates not in the Top 25:** CWE-327 (broken cryptography) and CWE-611 (XXE) are in neither the 2024 nor the 2025 list; they fall under `security-other`.

## Consequences
- [[Benchmark]] security cases are labeled with CWE IDs.
- [[Metrics]] reports per-category recall over the 11 CWE entries, the 7 logic categories ([[ADR-019 Logic bug taxonomy]]), and the `security-other` rate.
- A long category list makes classification harder; the gap between location-only and category-correct recall measures that cost.
