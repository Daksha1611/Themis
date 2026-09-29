---
type: decision
status: accepted
tags: [decision]
related:
  - "[[Webhook Service]]"
  - "[[GitHub Integration]]"
  - "[[Storage]]"
  - "[[httpx]]"
  - "[[PyJWT]]"
  - "[[pydantic-settings]]"
  - "[[uvicorn]]"
  - "[[psycopg]]"
---

# ADR-020 M1 runtime dependencies

## Context
Milestone 1 needs libraries not in the original stack: an async HTTP client for GitHub API calls, JWT signing for GitHub App auth, typed config from environment variables, an ASGI server for FastAPI, and a PostgreSQL driver for [[SQLAlchemy]].

## Decision
- [[httpx]]: all GitHub API calls ([[GitHub Integration]]). Async-native.
- [[PyJWT]] with its `crypto` extra (cryptography): RS256 GitHub App JWTs.
- [[pydantic-settings]]: `app/config.py`, all config from environment variables.
- [[uvicorn]]: ASGI server for the [[Webhook Service]].
- [[psycopg]] 3: PostgreSQL driver for SQLAlchemy, async mode (`postgresql+psycopg://`).

Core packages are pinned to exact versions in `pyproject.toml`.

## Alternatives considered
- `requests` instead of httpx: blocks the async event loop.
- asyncpg instead of psycopg 3: not chosen by the project owner.

## Consequences
- Five more packages to keep pinned and upgrade deliberately.
- psycopg supports both sync and async use, so future sync scripts can use the same driver.
