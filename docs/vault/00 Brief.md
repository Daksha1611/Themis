---
name: 00 Brief
description: "Mandatory first read every session: current milestone, hard constraints, decisions most easily broken, blocking questions."
type: project
status: in-progress
tags: [project]
related:
  - "[[00 Index]]"
  - "[[Current Status]]"
  - "[[Open Questions]]"
  - "[[09 External Facts]]"
---

# Brief

> Read this first, every session. It is a pointer and a guardrail, not a summary: details live in the linked notes.

## Project
Themis is a GitHub App that reviews Python pull requests for logic bugs and security issues. A reliability layer (benchmark, eval harness, CI gate) measures review quality, so every design decision is backed by real numbers.

## Current phase: finishing v1 (three-week plan from 2026-10-28)
**Plan:** [[ADR-030 v1 finish plan and scope cuts]], [[Roadmap]].
- **Week 1:** M4 wired behind `CONTEXT_BUDGET`; M4 runs in the background; M5 from cached findings.
- **Week 2:** the M4 result, M6, M7 and deployment.
- **Week 3:** holdout labelling, final holdout runs, results page and demo.

**State:** M1–M3 are done.
- **Dev baseline:** v2, J 0.327 (v1 0.435; the difference is within run-to-run noise): [[baseline-dev-2026-10-06-v2]].
- **Evaluation method:** k = 3 runs per configuration, compared with a paired permutation test and bootstrap CI ([[ADR-029 Aggregated evaluation]]).
- **M4:** context is off by default; with it off, prompts are byte-identical to v2's. The M4 plan runs with `python -m evals.schedule next` (about 9 days of quota).
- **M5:** finding-level classifiers failed ([[precision-filter-dev-2026-10-29]]). The pivot is to consistency ([[ADR-031 Consistency-based precision filter]]); the Step 1 gate is not met ([[agreement-dev-2026-10-29]]).

Details: [[Current Status]].

## Hard constraints
- Python repositories only ([[ADR-001 Python-only v1]]).
- Logic bugs and security issues only, never style ([[ADR-002 Bugs and security only]]).
- Free tiers only: no paid LLM spend, now or later ([[ADR-021 Free-tier four-provider LLM cascade]]).
- Public repositories only: diffs go unmasked to free-tier providers, some of which may use submitted data. Secret masking (Q49) comes before any private-repo support.
- No new technology, dependency or pattern without proposing it first, then an ADR before any code.
- v1 non-goals: other languages, style or lint comments, an MCP server, Prometheus and Grafana, anything not in the spec ([[Non-Goals]]).

## Decisions most easily broken by accident
- `confidence` comes from the precision filter, never the LLM. The LLM's own number is `raw_llm_confidence`: stored, never used to filter, never shown ([[ADR-016 Confidence comes from the precision filter, not the LLM]]).
- The precision filter trains on dev-split cases only, never holdout ([[ADR-017 Dev-split-only training data for the precision filter]]).
- The holdout split is run only at milestones ([[ADR-007 dev-holdout benchmark split]]). The M3 runner must refuse it without `--i-know-this-is-holdout`.
- Splits are frozen: no case ever moves between dev and holdout; holdout is labelled only after prompt tuning is frozen.
- `08 Results/` holds numbers from real runs only ([[08 Results/README|Results README]]).
- The vault, `docs/flow.md` and the code must agree. `scripts/check_vault.py` fails CI when they drift.
- Outside-world facts (model IDs, free-tier limits, versions) expire: check [[09 External Facts]] and re-verify anything older than 30 days.

## Open questions blocking work
- None blocking.
- **Do not edit the review-path modules** (`REVIEW_PATH_MODULES` in `evals/runner.py`) or anything that changes the rendered prompts while the M4 runs are in progress: an open run refuses to resume after any change.
- Deferred: **Q58** security benchmark track (post-v1, ADR-030), **Q59** regression-test validation

All questions: [[Open Questions]].

## Where to look next
- [[00 Index]]: every note, by section
- [[Architecture Overview]]: components, built versus planned
- [[Benchmark]], [[Eval Harness]], [[Metrics]]: the M3 work
- `docs/flow.md`: what the code does. `docs/decision.md`: why each change was made
- [[Session Log]]: what each session did
