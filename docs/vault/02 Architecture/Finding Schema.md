---
type: component
status: planned
tags: [component]
related:
  - "[[Review Graph]]"
  - "[[Precision Filter]]"
  - "[[Eval Harness]]"
  - "[[Storage]]"
  - "[[Pydantic]]"
  - "[[ADR-009 OWASP Top 10 security taxonomy]]"
---

# Finding Schema

**Purpose:** make every finding a typed object. Never free text.

**Responsibilities**
- Define `Finding` with fields: file, line, category, severity, message, confidence
- Security findings also carry an OWASP Top 10 category ([[ADR-009 OWASP Top 10 security taxonomy]])
- Define `ReviewResult` (fields not yet specified)

**Inputs:** produced by the [[Review Graph]].
**Outputs:** consumed by the [[Precision Filter]], comment posting, the [[Eval Harness]], and [[Storage]].

**Planned code location:** `app/schemas.py`.

**Dependencies:** [[Pydantic]].
