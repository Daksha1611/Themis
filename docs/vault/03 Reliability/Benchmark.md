---
type: reliability
status: planned
tags: [reliability]
related:
  - "[[Eval Harness]]"
  - "[[Metrics]]"
  - "[[ADR-007 dev-holdout benchmark split]]"
  - "[[ADR-009 OWASP Top 10 security taxonomy]]"
  - "[[ADR-011 Finding outcomes as precision-filter labels]]"
  - "[[ADR-017 Dev-split-only training data for the precision filter]]"
  - "[[ADR-019 Logic bug taxonomy]]"
  - "[[Benchmark Leakage]]"
  - "[[Label Noise]]"
  - "[[Eval Cost]]"
---

# Benchmark

**Purpose:** a labeled set of PRs to measure review quality against.

## Construction
- Mine bug-fix commits from ~5 mid-sized, well-tested Python repos
- Revert the fix to create a "buggy PR", labeled with the file and line range of the bug
- Label each case with its category: logic-bug taxonomy ([[ADR-019 Logic bug taxonomy]]) or OWASP Top 10 ([[ADR-009 OWASP Top 10 security taxonomy]])
- Include clean PRs with no known bug to measure false positives
- Target: 150–300 cases

## Repo selection criteria
- Actively maintained, well-tested Python projects with clear bug-fix commit conventions
- Mid-popularity preferred over famous repos, to reduce memorisation risk
- Target shapes: a web framework/library, a data tool, a CLI tool, a parsing/serialisation library, a smaller async library
- Commit range pinned to dates after the primary model's training cutoff
- The reasoning is recorded when repos are chosen. **Specific repos: still open.**

## Clean PRs
Merged PRs from the same repos whose touched files had no bug-fix commit for the following 6–12 months. **This is a heuristic, not proof** that a PR is bug-free. The size distribution of clean PRs matches the buggy ones, so the reviewer cannot learn "big diff means bug".

## Splits ([[ADR-007 dev-holdout benchmark split]])
- **60% dev** (for tuning) / **40% holdout** (run only at milestones)
- Stratified by repo and bug category, so both splits carry the same mix
- The holdout is larger than typical ML practice because the total case count is small and holdout numbers must be statistically meaningful
- The precision filter trains on dev-split findings only ([[ADR-017 Dev-split-only training data for the precision filter]])
- Outcome labels from benchmark repos must not leak into holdout ([[ADR-011 Finding outcomes as precision-filter labels]])

**Planned code location:** `evals/benchmark/` (`mine_commits.py`, `build_cases.py`, `data/dev` and `data/holdout` as JSONL).

Consumed by the [[Eval Harness]]. Risks: [[Benchmark Leakage]], [[Label Noise]], [[Eval Cost]].
