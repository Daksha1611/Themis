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
---

# Storage

**Purpose:** persist review runs and eval results.

**Responsibilities**
- Store review runs
- Store eval results

**Inputs:** review runs from the [[Job Queue]] worker; eval results from the [[Eval Harness]].
**Outputs:** stored records for later analysis.

**Planned code location:** not specified in the planned repo structure. `postgres` runs in `infra/` docker-compose.

**Dependencies:** [[PostgreSQL]], [[Docker]].
