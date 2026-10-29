---
name: pyyaml
description: "PyYAML: reads the eval run plans (evals/plans/*.yaml)."
type: tech
status: in-progress
tags: [tech]
related:
  - "[[Eval Harness]]"
  - "[[ADR-030 v1 finish plan and scope cuts]]"
version: 6.0.3 (pinned in the filter extra; read via uv pip show 2026-10-29)
---

# PyYAML

**What it is:** a YAML parser for Python.

**What it does in Themis:** `evals/schedule.py` reads run plans with `yaml.safe_load`. YAML 1.1 reads a bare `off` as false, so the plan quotes `cache: "off"`.

**Used by:** [[Eval Harness]]

**Version:** 6.0.3, also a dependency of [[transformers]].
