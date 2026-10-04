---
name: Open Questions
description: "Every open and resolved project question, numbered Q1 onward."
type: progress
status: in-progress
tags: [progress]
related:
  - "[[Current Status]]"
  - "[[Benchmark]]"
  - "[[Success Metrics]]"
  - "[[ADR-009 OWASP Top 10 security taxonomy]]"
  - "[[ADR-010 Prometheus and Grafana operational metrics]]"
  - "[[ADR-023 Arithmetic-or-numeric logic category]]"
  - "[[Label Noise]]"
---

# Open Questions

Each question is one bullet starting `**Q<n>.**`, and every number appears once across both sections (`scripts/check_vault.py` checks this). Questions that block current work say so in bold.

## Still open
- **Q47. TestClient migration.** Migrate from Starlette's `TestClient` (deprecated with httpx) to the newer async test approach before the test count grows further. `fastapi` and `starlette` are pinned until then.
- **Q48. Large-PR handling.** Diffs are truncated at 100,000 characters: a stopgap. Chunking or file-level splitting is needed.
- **Q49. Secret masking for private-repo support.** Build masking of secrets in diffs (and in the prompts, traces and thinking that contain them) before Themis reviews any private repository. **Private-repo support is out of scope for v1**: Themis is for public repositories only (README, Limitations). Decided 2026-10-02: sending *public* open-source diffs, including the M3 benchmark repos, to the free-tier providers and Langfuse cloud is acceptable without masking. Some providers' free-tier terms permit using submitted data to improve their products (Google's Gemini API free tier states this), which makes the public/private distinction load-bearing. Not blocking M3.
- **Q52b. Stable webhook URL.** Quick-tunnel URLs change on every cloudflared restart, so the App's webhook URL must be updated each time. A named tunnel, or the VPS (ADR-018), removes this.

- **Q58. Security benchmark track.** Mine vulnerability-fix commits from the PyPA advisory database / OSV for Python packages, as a separate security case set, because the M3 benchmark has too few security cases to measure security recall ([[Benchmark]], [[Metrics]]; the M6 security work: [[Review Graph]] security pass, [[ADR-022 CWE Top 25 security taxonomy]]). **Target: M6.**
- **Q59. Regression-test validation.** Use each fix commit's regression test to confirm a case is genuine (the test fails on the reverted source and passes on the fix). Costly: requires each repo's environment at each commit. Candidate for a validated subset ([[Benchmark]], [[Label Noise]]). Not for M3.


## Resolved

### Document conventions
- **Q1.** decision.md and flow.md live in `docs/`. Kept.
- **Q2.** `tags: [type]` without `#`. Kept.
- **Q3.** `related:` as a list of quoted wikilinks. Kept.
- **Q4.** Decision notes use `status: accepted | superseded`; status values per type are in the [[Glossary]].
- **Q5.** `00 Index` is `project`; Results README is `reliability`. Kept.
- **Q6.** Risk and stack notes started as `planned`. Since 2026-10-02 their status follows the per-type meanings in the [[Glossary]]: for stack notes, whether the package is installed and in use; for risks, how far the mitigation is in place.

### Architecture
- **Q7.** Guardrails run twice: sanitize before the graph, validate after; never skip a review → [[Guardrails]]
- **Q8.** New component owns App auth, diff fetch, comment posting → [[GitHub Integration]]
- **Q9.** `app/storage/` with SQLAlchemy models and Alembic migrations → [[ADR-012 Alembic for schema migrations]]
- **Q10.** Tracing in `app/observability/`; drift in `evals/drift/` plus a scheduled workflow → [[Tracing]], [[Drift Monitoring]]
- **Q11.** Langfuse cloud, free tier → [[ADR-013 Langfuse cloud over self-hosting]]
- **Q12.** Index on install, incrementally per PR, manually on demand → [[ADR-014 Incremental repo indexing]]
- **Q13.** Local sentence-transformers embeddings; Qdrant native sparse vectors with RRF → [[ADR-015 Local embeddings and Qdrant native hybrid search]]
- **Q14.** Context Builder outputs a Pydantic `ReviewContext` → [[Context Builder]], [[Finding Schema]]
- **Q15.** `ReviewResult` fields defined → [[Finding Schema]]
- **Q16.** Severity enum; confidence 0.0–1.0 from the precision filter, never the LLM → [[ADR-016 Confidence comes from the precision filter, not the LLM]]

### Precision filter
- **Q17.** Threshold tuned by a precision-recall sweep, configurable; default ADR once real data exists → [[Precision Filter]]
- **Q18.** Compare `microsoft/codebert-base` and `deberta-v3-small` as an ablation row → [[Precision Filter]], [[Ablation Table]]
- **Q19.** Labels from dev-split runs only, enforced in code → [[ADR-017 Dev-split-only training data for the precision filter]]

### Benchmark and metrics
- **Q21.** 60% dev / 40% holdout, stratified by repo and category → [[Benchmark]], [[ADR-007 dev-holdout benchmark split]]
- **Q22.** Clean PRs: files with no bug fix for 6–12 months (heuristic), size-matched → [[Benchmark]]
- **Q23.** Hit = within labeled range ±3 lines and correct category; exact-line accuracy secondary → [[Metrics]]
- **Q24.** Injection resistance via matched pairs → [[Metrics]]
- **Q26.** Own risk note → [[Benchmark Leakage]]

### Reliability layer
- **Q27.** Gate compares against main's last run in a separate eval database; −3 pp precision / −5 pp recall → [[CI Quality Gate]]
- **Q28.** Eval gate on in-repo branches only (50-case dev subset); forks run unit tests; full dev nightly → [[CI Quality Gate]]
- **Q29.** Weekly drift on the fixed subset: models in use plus one cheaper, one stronger → [[Drift Monitoring]]
- **Q30.** Ablation on holdout once at the end, with dev numbers alongside → [[Ablation Table]]
- **Q31.** Results page deployed to GitHub Pages by an Actions build artifact from `evals/report.py` → [[Ablation Table]]
- **Q32.** ruff, mypy, pytest (+ pytest-asyncio), pytest-cov → [[CI Quality Gate]]

### Operations
- **Q33.** Small paid VPS with Docker Compose and Caddy → [[ADR-018 Paid VPS over free tier hosting]]

### Prior art (resolved 2026-09-28)
- **Q34.** OWASP Top 10 taxonomy → [[ADR-009 OWASP Top 10 security taxonomy]] (superseded by [[ADR-022 CWE Top 25 security taxonomy]])
- **Q35.** Prometheus + Grafana → [[ADR-010 Prometheus and Grafana operational metrics]] (superseded for v1, see Q41)
- **Q36.** Outcome labels → [[ADR-011 Finding outcomes as precision-filter labels]]

### Raised by ADR-009 to ADR-011
- **Q37.** OWASP edition: OWASP Top 10 (2021) was pinned, then the taxonomy was replaced by CWE Top 25 (Q37b) → [[ADR-022 CWE Top 25 security taxonomy]]
- **Q38.** Logic bugs get a seven-category taxonomy → [[ADR-019 Logic bug taxonomy]]
- **Q39.** `security-other` with a required subcategory; frequency tracked → [[Finding Schema]], [[Metrics]]
- **Q40.** No longer applies in v1 (Prometheus deferred) → [[ADR-010 Prometheus and Grafana operational metrics]]
- **Q41.** ADR-010 superseded for v1, deferred to post-v1 stretch goals → [[ADR-010 Prometheus and Grafana operational metrics]]
- **Q42.** Validated / dismissed signal definitions; raw signals kept separate from labels → [[ADR-011 Finding outcomes as precision-filter labels]]
- **Q43.** Outcome labels reframed as a pilot, not a data engine → [[ADR-011 Finding outcomes as precision-filter labels]]

### Milestones (resolved 2026-09-30 and 2026-10-01)
- **Q44.** Alembic initialised in M2 pre-work. Bootstrap removed. Migration confirmed → [[ADR-012 Alembic for schema migrations]]
- **Q45.** GitHub App registered (`themis-reviewer-daksha`), installed on `Daksha1611/themis-test-repo`; JWT and installation token verified against GitHub.
- **Q46.** Langfuse cloud (EU) keys set; `auth_check()` passes.
- **Q50.** GitHub App now has Contents: Read-only (required for diff fetching; missing from the original spec) → [[GitHub Integration]]
- **Q51.** OpenRouter spending limit: no longer applicable. Free tiers only, four-provider cascade → [[ADR-021 Free-tier four-provider LLM cascade]]
- **Q52.** Webhook tunnel restarted and connected; GitHub deliveries reach the API (live test 2026-10-01). Stable-URL follow-up is Q52b.
- **Q53.** Machine clock fixed (`set-local-rtc 0`, `chronyc makestep`); skew vs GitHub 1 s; App JWT accepted.

### M3 decisions (resolved 2026-10-03)
- **Q60.** Clean cases: SZZ-style line-level rule, same filters as buggy, size-matched per bucket; FP rate per size bucket → [[Benchmark]], [[Metrics]]
- **Q61.** Category labels by hand on dev (labelling tool; holdout only after tuning is frozen); frozen splits; label noise = dropped share → [[Benchmark]]. **Amended 2026-10-03:** the owner could not hand-label, so the development assistant labelled the dev split after reading each case's upstream PR and issue threads (read-only). The limitation is stated in [[Benchmark]]; report: [[label-report-dev-2026-10-03]]
- **Q62.** Strict recall = a finding on any range recorded as holding the bug (primary plus contested ranges); three tiers reported (lenient, strict, primary-only); the chance baseline is scored on all three → [[Metrics]]
- **Q64.** Baseline run budget: the dev run spans two days with `--resume`, all on the pinned model, configuration unchanged. Cases run in a shuffled order with a recorded seed; the summary records the cases per session and day, and whether the model identifier stayed identical → [[Eval Harness]], [[Free Tier Throughput]]
- **Q63.** Run-to-run variance (measured 2026-10-04 by a no-cache rerun of dev baseline v1): McNemar disagreements of 6/80 for detection, 19/80 for category-correct and 12/41 for clean flags, none significant. These are the ablation noise floor → [[Metrics]]
- **Q65.** Line coordinates: numbered diff, new-file line rule, line validation, one validation retry → [[ADR-026 Numbered diffs and validated output]]
- **Q25.** Targets (holdout): J ≥ 0.60, clean flag rate ≤ 20%, precision ≥ 80%, strict category-correct recall ≥ 60%, cost ≤ 3× baseline, p95 latency ≤ 30 s; improvements must be McNemar-significant and above run-to-run noise → [[Success Metrics]]

### M3 decisions (resolved 2026-10-02)
- **Q20.** Benchmark repos: five, `pallets/click`, `agronholm/anyio`, `fastapi/fastapi`, `marshmallow-code/marshmallow`, `Textualize/rich`; httpx and httpcore dropped. Micro and macro recall both reported; security recall flagged as not statistically meaningful (Q58) → [[Benchmark]], [[Metrics]]
- **Q55.** `arithmetic-or-numeric` added with shared precedence rules → [[ADR-023 Arithmetic-or-numeric logic category]]
- **Q56.** Size filter counts package source only; the buggy PR reverts package source only → [[Benchmark]]

### M3 pre-work (resolved 2026-10-01)
- **Q37b.** Security taxonomy: CWE Top 25 (2024 edition), Python-reachable subset, replaces OWASP → [[ADR-022 CWE Top 25 security taxonomy]]
- **Q54.** Categories constrained: the prompt lists every allowed category; `Finding` rejects others (invalid → parse error). Live check on the test PRs returned only taxonomy categories.
