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
  - "[[Eval Cost]]"
---

# Eval Harness

**Purpose:** replay the [[Benchmark]] through Themis offline.

- Runs the full review path ([[Context Builder]] → [[Review Graph]] → [[Precision Filter]]) offline against the benchmark
- Caches LLM calls made through the [[LLM Client]]
- Computes [[Metrics]] and produces reports
- Eval results are stored in [[Storage]]

**Planned code location:** `evals/runner.py`, `evals/metrics.py`, `evals/report.py`.

Risk: [[Eval Cost]].
