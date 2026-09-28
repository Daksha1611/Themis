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
---

# Finding Schema

**Purpose:** make every finding a typed object. Never free text.

**Responsibilities**
- Define `Finding` with fields: file, line, category, severity, message, confidence
- Define `ReviewResult` (fields not yet specified)

**Inputs:** produced by the [[Review Graph]].
**Outputs:** consumed by the [[Precision Filter]], comment posting, the [[Eval Harness]], and [[Storage]].

**Planned code location:** `app/schemas.py`.

**Dependencies:** [[Pydantic]].
