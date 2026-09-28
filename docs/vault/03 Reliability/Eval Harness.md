---
type: reliability
status: planned
tags: [reliability]
related:
  - "[[Benchmark]]"
  - "[[Metrics]]"
  - "[[Job Queue]]"
  - "[[LLM Client]]"
  - "[[Storage]]"
  - "[[Precision Filter]]"
  - "[[Guardrails]]"
  - "[[Ablation Table]]"
  - "[[Benchmark Leakage]]"
  - "[[Eval Cost]]"
---

# Eval Harness

**Purpose:** replay the [[Benchmark]] through Themis offline.

- Runs the full review path ([[Context Builder]] → [[Guardrails]] → [[Review Graph]] → [[Precision Filter]]) offline against the benchmark
- Caches LLM calls made through the [[LLM Client]]
- Computes [[Metrics]] and produces reports
- Sweeps [[Precision Filter]] thresholds to produce a precision-recall curve
- Runs injection cases from `evals/injection/` as matched pairs (the same diff with and without injection)
- Eval results go to the separate eval database in [[Storage]]
- `evals/report.py` generates the public results page, deployed to GitHub Pages by GitHub Actions as a build artifact ([[Ablation Table]])

**Planned code location:** `evals/runner.py`, `evals/metrics.py`, `evals/report.py`.

Risks: [[Benchmark Leakage]], [[Eval Cost]].
