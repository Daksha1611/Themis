---
type: tech
status: in-progress
tags: [tech]
related:
  - "[[Storage]]"
  - "[[ADR-012 Alembic for schema migrations]]"
  - "[[SQLAlchemy]]"
version: 1.20.0
---

# Alembic

**What it is:** Database migration tool for SQLAlchemy.

**What it does in Themis:** Manages PostgreSQL schema migrations in `app/storage/migrations/`.

**Used by:** [[Storage]], [[ADR-012 Alembic for schema migrations]], [[SQLAlchemy]]

**Version:** 1.20.0 (installed 2026-09-30).

Initialised in M2 at `app/storage/migrations/`. `alembic.ini` leaves `sqlalchemy.url` empty; `env.py` reads `DATABASE_URL`. Migrations run synchronously with the same `postgresql+psycopg://` URL the async app uses (psycopg 3 serves both modes).
