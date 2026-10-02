---
name: Eval Harness
description: "Offline replay of the benchmark through the real review path, with a response cache."
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

- Runs the same review path the worker runs, offline against the benchmark: today the baseline pass (`run_baseline_review`), later the full path ([[Context Builder]] → [[Guardrails]] → [[Review Graph]] → [[Precision Filter]]). Never a separate copy of the logic
- Caches LLM calls made through the [[LLM Client]]
- Computes [[Metrics]] and produces reports
- Sweeps [[Precision Filter]] thresholds to produce a precision-recall curve
- Runs injection cases from `evals/injection/` as matched pairs (the same diff with and without injection)
- Eval output goes to **two destinations** (decided 2026-10-02):
  - **Case-level results** (one record per benchmark case; large; regenerable) → `results.jsonl` files. This is the M3 artifact. LLM responses behind them are cached in SQLite at `evals/.cache/responses.db`.
  - **Run-level summary metrics** (one row per eval run: precision, recall, cost, latency, git SHA, split, timestamp; small; must persist) → the dedicated eval database ([[Storage]]), consumed by the [[CI Quality Gate]] in M7 to compare a PR against main's last recorded run.
  - `results.jsonl` is written incrementally (checkpointed), so an interrupted run resumes.
- `evals/report.py` generates the public results page, deployed to GitHub Pages by GitHub Actions as a build artifact ([[Ablation Table]])

**Planned code location:** `evals/runner.py`, `evals/metrics.py`, `evals/report.py`.

Risks: [[Benchmark Leakage]], [[Eval Cost]].
