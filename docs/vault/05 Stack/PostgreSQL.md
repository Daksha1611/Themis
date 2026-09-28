---
type: tech
status: planned
tags: [tech]
related:
  - "[[Storage]]"
  - "[[Eval Harness]]"
version:
---

# PostgreSQL

**What it is:** Relational database.

**What it does in Themis:** Stores review runs, finding outcomes, and eval results. Accessed through SQLAlchemy, migrated with Alembic. CI and drift runs use a separate eval database. Neon free tier is an option to shrink the VPS.

**Used by:** [[Storage]], [[Eval Harness]], [[CI Quality Gate]], [[SQLAlchemy]], [[Alembic]], [[ADR-018 Paid VPS over free tier hosting]]

**Version:** not installed yet.
