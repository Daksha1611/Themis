---
type: component
status: planned
tags: [component]
related:
  - "[[Job Queue]]"
  - "[[Eval Harness]]"
  - "[[Finding Schema]]"
  - "[[Precision Filter]]"
  - "[[GitHub Integration]]"
  - "[[CI Quality Gate]]"
  - "[[PostgreSQL]]"
  - "[[SQLAlchemy]]"
  - "[[Alembic]]"
  - "[[Docker]]"
  - "[[ADR-011 Finding outcomes as precision-filter labels]]"
  - "[[ADR-012 Alembic for schema migrations]]"
---

# Storage

**Purpose:** persist review runs, finding outcomes, and eval results.

**Responsibilities**
- Store review runs (`ReviewResult`)
- Store finding-outcome signals from [[GitHub Integration]]. Raw signals are stored separately from the derived label ([[ADR-011 Finding outcomes as precision-filter labels]]).
- Store eval results. CI and drift runs use a **separate eval database**, not production. It holds each main-branch eval run's metrics for the [[CI Quality Gate]].

**Inputs:** review runs from the [[Job Queue]] worker; outcome signals from [[GitHub Integration]]; eval results from the [[Eval Harness]].
**Outputs:** stored records; outcome labels for the [[Precision Filter]].

**Planned code location:** `app/storage/` ([[ADR-012 Alembic for schema migrations]]):
- `models.py` ([[SQLAlchemy]])
- `repository.py`
- `migrations/` ([[Alembic]])

**Dependencies:** [[PostgreSQL]], [[Docker]]. Neon free tier is an option ([[ADR-018 Paid VPS over free tier hosting]]).
