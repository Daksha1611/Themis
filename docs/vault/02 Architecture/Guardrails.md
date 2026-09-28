---
type: component
status: planned
tags: [component]
related:
  - "[[Review Graph]]"
  - "[[Context Builder]]"
  - "[[Metrics]]"
  - "[[Python]]"
---

# Guardrails

**Purpose:** stop hidden instructions in the reviewed code from steering the reviewer.

**Responsibilities**
- Detect prompt injection hidden in code comments, docstrings, and PR descriptions

**Inputs:** code comments, docstrings, and PR descriptions from the PR under review.
**Outputs:** a detection result. What happens on detection is not yet specified.

**Planned code location:** `app/guardrails/`. Adversarial test PRs in `evals/injection/`.

**Dependencies:** receives content from the [[Context Builder]]; relationship to the [[Review Graph]] (before, after, or both) is not yet specified. Measured by injection resistance in [[Metrics]].
