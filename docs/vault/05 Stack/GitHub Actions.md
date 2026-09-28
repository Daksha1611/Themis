---
type: tech
status: planned
tags: [tech]
related:
  - "[[CI Quality Gate]]"
version:
---

# GitHub Actions

**What it is:** GitHub's CI/CD service.

**What it does in Themis:** Runs `ci.yml` (ruff, mypy, pytest), `eval-gate.yml` (50-case dev subset per PR from branches in this repo), a nightly full dev-split eval, the weekly drift workflow, and the GitHub Pages deploy of the results page.

**Used by:** [[CI Quality Gate]], [[Drift Monitoring]], [[Ablation Table]], [[ruff]], [[mypy]], [[pytest]]

**Version:** not installed yet.
