---
type: component
status: planned
tags: [component]
related:
  - "[[Job Queue]]"
  - "[[Eval Harness]]"
  - "[[Finding Schema]]"
  - "[[PostgreSQL]]"
  - "[[Docker]]"
  - "[[Precision Filter]]"
  - "[[ADR-011 Finding outcomes as precision-filter labels]]"
---

# Storage

**Purpose:** persist review runs and eval results.

**Responsibilities**
- Store review runs
- Store eval results
- Store the outcomes of posted findings (resolved or dismissed), used as [[Precision Filter]] labels ([[ADR-011 Finding outcomes as precision-filter labels]])

**Inputs:** review runs from the [[Job Queue]] worker; eval results from the [[Eval Harness]].
**Outputs:** stored records for later analysis.

**Planned code location:** not specified in the planned repo structure. `postgres` runs in `infra/` docker-compose.

**Dependencies:** [[PostgreSQL]], [[Docker]].
