---
name: GitHub Actions
description: "GitHub Actions: runs the CI workflow; eval, drift and results-page workflows later."
type: tech
status: done
tags: [tech]
related:
  - "[[CI Quality Gate]]"
  - "[[pytest-asyncio]]"
version: "actions/checkout@v4, actions/setup-python@v5, runner ubuntu-latest (from ci.yml)"
---

# GitHub Actions

**What it is:** GitHub's CI/CD service.

**What it does in Themis:** Runs `.github/workflows/ci.yml` on every push and pull request: the `test` job (ruff, ruff format, mypy, pytest) and the `vault-check` job (`scripts/check_vault.py`). In use since M1.
**Planned:** `eval-gate.yml` (50-case dev subset per PR from branches in this repo), a nightly full dev-split eval, the weekly drift workflow, and the GitHub Pages deploy of the results page.

**Used by:** [[CI Quality Gate]], [[Drift Monitoring]], [[Ablation Table]], [[ruff]], [[mypy]], [[pytest]]

**Version:** `actions/checkout@v4`, `actions/setup-python@v5` (Python 3.12), runner `ubuntu-latest`, as pinned in `ci.yml` (read 2026-10-02).
