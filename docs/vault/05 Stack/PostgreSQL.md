---
type: tech
status: in-progress
tags: [tech]
related:
  - "[[Storage]]"
  - "[[Eval Harness]]"
version: server image postgres:16-alpine
---

# PostgreSQL

**What it is:** Relational database.

**What it does in Themis:** Stores review runs, finding outcomes, and eval results. Accessed through SQLAlchemy, migrated with Alembic. CI and drift runs use a separate eval database. Neon free tier is an option to shrink the VPS.

**Used by:** [[Storage]], [[Eval Harness]], [[CI Quality Gate]], [[SQLAlchemy]], [[Alembic]], [[ADR-018 Paid VPS over free tier hosting]]

**Version:** server image postgres:16-alpine (recorded 2026-09-29).
