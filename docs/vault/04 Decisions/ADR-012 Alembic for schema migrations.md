---
name: ADR-012 Alembic for schema migrations
description: "Decision: storage lives in app/storage with SQLAlchemy models and Alembic migrations."
type: decision
status: accepted
tags: [decision]
related:
  - "[[Storage]]"
  - "[[SQLAlchemy]]"
  - "[[Alembic]]"
  - "[[PostgreSQL]]"
---

# ADR-012 Alembic for schema migrations

## Context
[[Storage]] had no code location, and the PostgreSQL schema must evolve as review runs, eval results, and finding outcomes are added.

## Decision
Storage code lives in `app/storage/`:
- `models.py`: [[SQLAlchemy]] models
- `repository.py`: data access
- `migrations/`: [[Alembic]] schema migrations

## Alternatives considered
- None stated.

## Consequences
- SQLAlchemy and Alembic join the tech stack.
- Schema changes are made through Alembic migrations.
