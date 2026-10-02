---
name: CI Quality Gate
description: "What CI checks: lint, types, tests and the vault check today; the eval gate against main later."
type: reliability
status: in-progress
tags: [reliability]
related:
  - "[[Eval Harness]]"
  - "[[Metrics]]"
  - "[[Storage]]"
  - "[[GitHub Actions]]"
  - "[[ruff]]"
  - "[[mypy]]"
  - "[[pytest]]"
  - "[[pytest-cov]]"
  - "[[ADR-007 dev-holdout benchmark split]]"
  - "[[Eval Cost]]"
---

# CI Quality Gate

**Purpose:** block changes that make review quality worse.

## The gate
- Compares against **main**, not a fixed number. Each eval run's **run-level summary** (precision, recall, cost, latency, git SHA, split, timestamp) is stored as one row in the dedicated eval database ([[Storage]]); the gate (M7) compares the PR's run against main's last recorded row. Case-level results stay in `results.jsonl` files and are not used by the gate ([[Eval Harness]]).
- Fails if precision drops more than **3 percentage points** or recall more than **5**, relative to main's last recorded run.
- Prints the full comparison in the PR check output, so failures explain themselves.

## What runs when
- **PRs from branches in this repo:** eval on a fixed random subset of **50 dev-split cases**.
- **Fork PRs:** unit tests only. **Limitation:** fork PRs cannot access repository secrets, so the eval gate cannot run on them.
- **Nightly:** the full dev split.

## Lint, tests and vault check (`ci.yml`, built)
Runs on every push and pull request:
- `test` job: [[ruff]] (lint and format), [[mypy]] (strict, `app/`), [[pytest]] with [[pytest-asyncio]].
- `vault-check` job: `python scripts/check_vault.py`, which fails the build when the vault, `docs/flow.md` and the code drift apart.

[[pytest-cov]] is installed but CI does not run coverage yet.

**Code location:** `.github/workflows/ci.yml` (built), run by [[GitHub Actions]]. Planned: `.github/workflows/eval-gate.yml` for the gate above.

Decision: [[ADR-007 dev-holdout benchmark split]]. Risk: [[Eval Cost]].
