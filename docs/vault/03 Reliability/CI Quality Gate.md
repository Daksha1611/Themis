---
type: reliability
status: planned
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
- Compares against **main**, not a fixed number. Each main-branch eval run's metrics are stored in the separate eval database ([[Storage]]).
- Fails if precision drops more than **3 percentage points** or recall more than **5**, relative to main's last recorded run.
- Prints the full comparison in the PR check output, so failures explain themselves.

## What runs when
- **PRs from branches in this repo:** eval on a fixed random subset of **50 dev-split cases**.
- **Fork PRs:** unit tests only. **Limitation:** fork PRs cannot access repository secrets, so the eval gate cannot run on them.
- **Nightly:** the full dev split.

## Lint and tests (`ci.yml`)
[[ruff]] (lint + format), [[mypy]] (types), [[pytest]] with pytest-asyncio, [[pytest-cov]].

**Planned code location:** `.github/workflows/eval-gate.yml` and `.github/workflows/ci.yml`, run by [[GitHub Actions]].

Decision: [[ADR-007 dev-holdout benchmark split]]. Risk: [[Eval Cost]].
