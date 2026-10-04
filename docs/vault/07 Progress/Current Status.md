---
name: Current Status
description: "Where the project stands: current milestone, what is done, what is next."
type: progress
status: in-progress
tags: [progress]
related:
  - "[[Session Log]]"
  - "[[Open Questions]]"
  - "[[00 Index]]"
---

# Current Status

**Phase:** M3 in progress. Steps 2–3 built (238 cases; SZZ clean rule; frozen splits). The dev split is labelled (Step 3b; [[label-report-dev-2026-10-03]]). The owner verified a stratified 25-case sample: 25/25 agreement on every field. Steps 4–7 are done: cache, runner, metrics, and the dev baseline run ([[baseline-dev-2026-10-03]]). Metrics redesigned ([[ADR-025 Detection-first metrics]]); the current baseline is [[baseline-dev-2026-10-04]]: J 0.435 (chance 0). **Waiting for the owner:** Q65 (line-coordinate convention) and Q25 (targets). M4 not started.
**Last updated:** 2026-10-03 (dev-split labels)

New sessions start with [[00 Brief]].

**Done (M2)**
- Alembic-managed schema; startup bootstrap gone ([[Storage]])
- Free-tier four-provider LLM cascade ([[ADR-021 Free-tier four-provider LLM cascade]], [[LLM Client]])
- Final `Finding` / `ReviewResult` schema with `confidence` vs `raw_llm_confidence` ([[Finding Schema]])
- Diff fetch, baseline pass, PR review posting ([[GitHub Integration]], [[Review Graph]])
- Langfuse tracing audited against real traces: provider, tokens, cost and model thinking captured ([[Tracing]])
- 46 tests; ruff, mypy, CI green
- **Live test, 2026-10-01** on `Daksha1611/themis-test-repo`, delivered by GitHub through the tunnel:
  - PR #2 (planted bugs): 3 line comments, one per bug (off-by-one, missing None check, divide-by-zero); Groq `openai/gpt-oss-120b`; 6.1 s
  - PR #3 (clean change): "no issues found" comment; Groq; 2.5 s

**Done (M3 so far)**
- CWE Top 25 (2024) security taxonomy ([[ADR-022 CWE Top 25 security taxonomy]]); ADR-009 superseded
- Categories constrained in prompt and validated in `Finding` (Q54); 73 tests
- Test repo cleaned (all PRs closed, branches deleted)
- Repo verification table ([[Benchmark]]); leakage date distribution ([[Benchmark Leakage]])

**Done (vault audit and hardening, 2026-10-02)**
- Vault corrected against the code and the live system: superseded decisions, component notes, statuses, stack versions, open-question numbering, metric definitions
- [[00 Brief]] (mandatory first read) and [[09 External Facts]] (outside-world facts with verification dates, re-checked live on 2026-10-02)
- `scripts/check_vault.py` with 21 tests; `vault-check` CI job. 94 tests in all
- OpenRouter's free model returned 429 (upstream rate limit) on 2026-10-02; the other three providers answered

**Done (M3 Step 3b: dev-split labels, 2026-10-03)**
- Q61 amended: the development assistant labelled all 143 dev cases after reading each case's upstream PR and issue threads, bot comments included. Read-only: GET requests only, nothing posted upstream. Limitation stated in [[Benchmark]].
- Buggy: 80 of 102 kept, 22 dropped (2 feature, 8 typing-only, 1 refactor, 2 not-a-bug, 9 other, 8 of them `external-compat`).
- Clean: 3 of 41 marked suspicious. One looks like the origin of two later click bugs; SZZ missed it.
- Macro-eligible categories (≥5 kept): type-or-contract 34, control-flow 17, concurrency-or-async 9, error-handling 7.
- Primary range clear in 48 of 80 kept cases; contested in 32 (Q62).
- New code: `fetch_evidence.py`, `write_labels.py`, `label_report.py`; 9 new tests, 128 in all.

**Done (owner decisions and verification sample, 2026-10-03)**
- Q62 closed: three recall tiers (lenient, strict = any bug-holding range, primary-only), with the chance baseline on all three ([[Metrics]]).
- [[Metrics]] now requires two caveats:
  - every false-positive rate carries the clean-case noise floor (3 of 41 suspicious, 7.3%);
  - macro recall is always reported with per-category counts.
- The SZZ code-movement limit is recorded in [[Benchmark Leakage]].
- `evals/benchmark/verify_sample.py` writes the owner's verification sample: 25 stratified kept cases plus 3 borderline ones, seed 20261003. Its `--score` mode computes the agreement rates.
- Anyio's PR-template example link (#123) removed from 19 cases' evidence lists; the fetcher now skips code blocks, comments and template examples. 137 tests.

- Owner verification recorded: 25/25 agreement on validity, category and primary range (95% Wilson lower bound 86.7%); borderline cases 3/3. The verdicts are the owner's, given after reviewing all 28 cases; the agent entered the ticks at the owner's instruction. The label report gained section 9.

**Done (M3 Steps 4–6, 2026-10-03)**
- [[ADR-024 Eval runs pin a single provider and model]]: `PinnedLLM` in `app/llm.py`; one attempt on the pinned model, never the cascade; production unchanged.
- `evals/cache.py` (SQLite response cache), `evals/runner.py` (scored set of 121, pacing, backoff, resume, holdout guard, dry run, `--cache-only`) and `evals/metrics.py` (three tiers × two modes, macro floor, precision, FP by size and repo with the noise floor, chance baseline, Wilson intervals).
- 36 new tests, 174 in all; `docs/flow.md` section 9 written.
- **Dry run:**
  - 121 cases; prompts 125,635 tokens (63% of 200K/day); the largest request is 3,751 of 8,000, so every case fits.
  - The run fits one day only if completions average ≤615 tokens; past `gpt-oss-120b` completions average ~822. The expected total (~225K) is over one day, so per the brief **no LLM call was made** (Q64).


**Done (M3 Step 7: dev baseline, 2026-10-03)**
- Q64: a two-day run with `--resume` was planned. In the event, the run finished in **one session** (~1 hour, 122 provider calls, 121 cases) with no daily-limit response.
- Pinned `groq/openai/gpt-oss-120b`; 100% of answered cases came from it, with an identical model ID throughout. The `--cache-only` rerun gave identical metrics with 0 provider calls.
- Strict category-correct recall 41/80 (51.2%); precision 75/109 (68.8%); clean FP 17/41 (41.5%).
- **The chance baseline beats the reviewer on location recall** (strict 95.0% vs 80.0%).
- Leak scan: 9/80 buggy and 2/41 clean diffs have issue references or telltale words in removed lines.

**Done (metric redesign, 2026-10-04)**
- Base rate: on average 81.2% of a buggy case's changed lines lie in its bug-holding ranges ±3 (46/80 cases at 100%), so location matching is non-discriminating.
- Strict-location misses (16):
  - 10 no findings;
  - 1 parse failure;
  - 2 cite removed lines by old-file number;
  - 2 on changed lines outside ±3;
  - 1 outside the diff.

  No systematic coordinate offset; the old-side convention gap is Q65.
- [[ADR-025 Detection-first metrics]]: J with a Newcombe interval, category-correct recall, precision and clean flag rate, all beside the chance baseline; location tolerance ±0/±1/±3 as diagnostics; exact McNemar for every run comparison.
- Masking (`mask-issue-refs-v1`) changed 7 cases. Exactly 7 LLM calls were made (114 cache hits). Leak-matched cases were not advantaged, and McNemar p = 1.0 on all three measures.
- Clean false positives: 20 findings on 17 cases; 11 are `type-or-contract`, 14 are medium severity; the 16–30-line bucket is flagged hardest (6/8). Two of the 3 suspicious clean cases were flagged.
- New baseline: J 0.435 (0.257–0.586) vs chance 0; category-correct 41/80 vs 34/80; precision 74/108 vs 94/243; clean flag rate 17/41 vs 41/41. 188 tests.

**Done (2026-10-04, while v2 waits for the Groq daily window)**
- Q63 noise floor: 6/80 detection, 19/80 category-correct, 12/41 clean flags (none significant). It was verified valid: identical review-path code and identical rendered prompts for all 121 cases.
- Run fingerprint: a code hash (eight review-path modules plus the diff transform) and a prompt hash (rendered prompts). `--resume` refuses on any change and uses the recorded case order. v2's fingerprint was backfilled from `4feea8e`, and it still matches.
- ADR-026 implemented; baseline v2 stopped at 6/121 on Groq's 200K tokens/day rolling limit, which is now confirmed.
- M4 groundwork ([[ADR-027 Eval-time repo context]]): a standalone context builder in `app/context/`, not wired into the review path. Retrieval eval [[context-retrieval-dev-2026-10-04]]:
  - symbol-definition recall 21.2% / 23.7% / 25.0% at 1K / 2K / 4K tokens;
  - 0 chunks from test, doc, changelog or CI paths;
  - embedding-cache hit rate 94.6%.

**Next**
- Resume v2: `.venv/bin/python -m evals.runner --split dev --resume`, after about 14:10 UTC on 2026-10-05.
- Then the v2 report: v1 vs the v1 rerun vs v2, the noise floor, McNemar, attribution, the sensitivity line and targets.
- Owner: whether retrieval needs a symbol-aware step before context is wired in (recall 25% at 4K).
- Q47 (TestClient), Q48 (large PRs), Q49 (secrets in traces), Q52b (stable webhook URL).
