---
type: reliability
status: planned
tags: [reliability]
related:
  - "[[Eval Harness]]"
  - "[[Metrics]]"
  - "[[GitHub Actions]]"
  - "[[ADR-007 dev-holdout benchmark split]]"
  - "[[Eval Cost]]"
---

# CI Quality Gate

**Purpose:** block changes that make review quality worse.

- [[GitHub Actions]] runs the [[Eval Harness]] on the **dev** split for every PR to the Themis repo
- Fails the build if precision or recall drops past a threshold (threshold not yet specified)

**Planned code location:** `.github/workflows/eval-gate.yml`. Lint and unit tests live separately in `.github/workflows/ci.yml`.

Decision: [[ADR-007 dev-holdout benchmark split]]. Risk: [[Eval Cost]].
