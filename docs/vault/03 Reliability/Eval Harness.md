---
name: Eval Harness
description: "Offline replay of the benchmark through the real review path, with a response cache."
type: reliability
status: in-progress
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

## Built (M3 Steps 4–6, 2026-10-03)
- **Runner:** `python -m evals.runner --split dev [--limit N] [--resume] [--no-cache] [--cache-only] [--dry-run] [--i-know-this-is-holdout]` (`evals/runner.py`).
  - Calls `run_baseline_review` with one pinned provider and model, cascade disabled ([[ADR-024 Eval runs pin a single provider and model]]).
  - **Neutral PR title (known eval/production difference):** every eval case gets the same title (`EVAL_PR_TITLE`, "Proposed change"), to prevent label leakage. The real commit subject ("Fix X") would describe the bug, and would tell buggy cases from clean ones. The eval therefore measures **diff-only review**. Production passes the real PR title, so production performance may differ.
- **Scored set:** kept buggy cases plus all clean cases. Dropped cases are never sent. Dev: 80 + 41 = 121.
- **Run fingerprint** (owner decision, 2026-10-04). `run.json` records two hashes:
  - the **code hash:** SHA-256 over the eight modules the review path imports (`REVIEW_PATH_MODULES`: `app/config.py`, `app/github/client.py`, `app/github/diff.py`, `app/graph/baseline.py`, `app/llm.py`, `app/observability/tracing.py`, `app/schemas.py`, `app/taxonomy.py`), plus the diff-transform version;
  - the **prompt hash:** SHA-256 over the rendered prompts of the full scored set, built through the `--dry-run` path. It catches eval-side changes outside those modules: the neutral title, masking, case data and labels.

  Per-file hashes are kept, along with the `case_order`. `--resume` refuses on any mismatch, naming which hash changed and, for the code, which files. It uses the recorded case order and never recomputes it. A run without a recorded fingerprint cannot be resumed. `--check-fingerprint` compares the latest open run with the current code and makes no calls.
- **Diff transform:** `mask_issue_refs()` (`mask-issue-refs-v1`, recorded in `run.json`; each record carries `diff_masked`) masks issue references in removed lines before review ([[Benchmark]]).
- **Run order** (Q64): shuffled with a fixed seed (`ORDER_SEED`, recorded in `run.json`), so a stop at the daily budget cannot line up with a repo, category or buggy/clean grouping. `--resume` rebuilds the same order.
  - Each record carries `started_at`, `finished_at` and its `session` (one runner invocation).
  - `run.json` lists the sessions with their stop reason.
  - `summary.json` lists the cases per session and per UTC day, the model identifiers per session, and whether they were identical.
- **Output:** `evals/results/<split>-<UTC time>-<sha7>/`, holding `run.json` (config, git SHA), `results.jsonl` (one record per case, written as each completes) and `summary.json` (all metrics, schema version 1, ready for the M7 eval database). The eval database itself is M7.
- **Cache** (`evals/cache.py`): SQLite `evals/.cache/responses.db`, git-ignored.
  - Key: SHA-256 of provider, model, full prompt messages, temperature and max_tokens.
  - Stores the full `LLMResponse`, reasoning included, plus the original call's latency.
  - `--cache-only` fails on the first miss (exit 4) without calling anything.
- **Pacing and limits:**
  - a 60-second token window keeps estimated tokens (prompt + `max_tokens`) under Groq's 8K/minute;
  - per-minute 429s back off (the provider's "try again in" hint, else exponential) and retry the same model;
  - a daily 429 checkpoints and exits 3 (`--resume` continues);
  - 413 or context-length errors are recorded as `failed: provider-limit`.
- **Dry run** (`--dry-run`): builds every prompt and reports per-case token estimates (LiteLLM `token_counter`, tiktoken `cl100k_base`: an estimate), the largest request, the total, and fit against the per-request ceiling and the daily budget. It calls nothing.
- **Holdout guard:** `--split holdout` prints a warning and refuses without `--i-know-this-is-holdout`.

- **Report** (`evals/report.py`): `python -m evals.report evals/results/<run_id>` writes `08 Results/baseline-<split>-<date>.md`, with every rate as k/n and a Wilson interval, the chance baseline beside each recall tier, and a required Caveats section.

**Not built yet:** threshold sweeps and injection pairs (later milestones).

**Code location:** `evals/runner.py`, `evals/cache.py`, `evals/metrics.py`, `evals/report.py`.

Risks: [[Benchmark Leakage]], [[Eval Cost]].
