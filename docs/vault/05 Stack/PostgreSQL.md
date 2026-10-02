---
name: PostgreSQL
description: "PostgreSQL: the database behind Storage."
type: tech
status: done
tags: [tech]
related:
  - "[[Storage]]"
  - "[[Eval Harness]]"
version: server image postgres:16-alpine
---

# PostgreSQL

**What it is:** Relational database.

**What it does in Themis:** Stores the `review_runs` table ([[Storage]]), accessed through SQLAlchemy and migrated with Alembic. Planned: finding-outcome signals, and the dedicated eval database holding one run-level summary row per eval run for the CI gate (M7). Case-level eval results are `results.jsonl` files, not Postgres. Neon free tier is an option to shrink the VPS.

**Used by:** [[Storage]], [[Eval Harness]], [[CI Quality Gate]], [[SQLAlchemy]], [[Alembic]], [[ADR-018 Paid VPS over free tier hosting]]

**Version:** server image postgres:16-alpine (recorded 2026-09-29).
