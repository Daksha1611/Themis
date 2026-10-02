---
name: Scope Creep
description: "Risk of building beyond the v1 scope."
type: risk
status: in-progress
tags: [risk]
related:
  - "[[Scope]]"
  - "[[Non-Goals]]"
  - "[[ADR-001 Python-only v1]]"
  - "[[ADR-002 Bugs and security only]]"
---

# Scope Creep

**Risk:** The biggest risk.

**Mitigation**
- Python only ([[ADR-001 Python-only v1]])
- Bugs + security only ([[ADR-002 Bugs and security only]]). Enforced in code: `Finding` rejects any category outside the taxonomy
- No stretch goals before everything ships ([[Non-Goals]])

**Affects:** [[Scope]], [[Non-Goals]], [[ADR-001 Python-only v1]], [[ADR-002 Bugs and security only]]
