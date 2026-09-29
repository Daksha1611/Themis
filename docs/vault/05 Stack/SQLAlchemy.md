---
type: tech
status: in-progress
tags: [tech]
related:
  - "[[Storage]]"
  - "[[ADR-012 Alembic for schema migrations]]"
  - "[[Alembic]]"
  - "[[PostgreSQL]]"
version: 2.1.1 (asyncio extra, greenlet 3.5.6)
---

# SQLAlchemy

**What it is:** Python SQL toolkit and ORM.

**What it does in Themis:** Defines the Storage models in `app/storage/models.py`.

**Used by:** [[Storage]], [[ADR-012 Alembic for schema migrations]], [[Alembic]], [[PostgreSQL]]

**Version:** 2.1.1 (recorded 2026-09-29), installed as `sqlalchemy[asyncio]` (greenlet 3.5.6) for async use.
