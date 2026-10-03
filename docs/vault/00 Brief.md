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

## Current milestone: M3, benchmark and eval harness
**Delivers:** 150–300 labeled cases (reverted bug fixes plus ~30% clean PRs) split 60/40 dev/holdout; a response cache; an eval runner over the real review path; metrics; the first baseline dev report in `08 Results/`.
**State:** Steps 2–3 built: 238 cases (168 buggy, 70 clean; dev 143 / holdout 95), SZZ clean rule. The dev split is labelled from upstream evidence: 80 of 102 buggy cases kept (Q61 amended; [[label-report-dev-2026-10-03]]). The owner verified a stratified 25-case sample of the labels: 25/25 agreement on validity, category and primary range ([[Benchmark]]). Q62 is decided: three recall tiers ([[Metrics]]). **Next:** M3 Steps 4–7 (cache, runner, metrics, baseline dev report). Details: [[Current Status]], [[Benchmark]].

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
- None open. Next gate: the owner's dev labelling pass before Steps 4–7 (cache, runner, metrics, baseline run).
- Not M3: **Q58** security benchmark track (M6), **Q59** regression-test validation

All questions: [[Open Questions]].

## Where to look next
- [[00 Index]]: every note, by section
- [[Architecture Overview]]: components, built versus planned
- [[Benchmark]], [[Eval Harness]], [[Metrics]]: the M3 work
- `docs/flow.md`: what the code does. `docs/decision.md`: why each change was made
- [[Session Log]]: what each session did
