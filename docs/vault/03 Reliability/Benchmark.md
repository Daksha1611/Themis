---
type: reliability
status: planned
tags: [reliability]
related:
  - "[[Eval Harness]]"
  - "[[Metrics]]"
  - "[[ADR-007 dev-holdout benchmark split]]"
  - "[[Label Noise]]"
  - "[[Eval Cost]]"
---

# Benchmark

**Purpose:** a labeled set of PRs to measure review quality against.

**Construction**
- Mine bug-fix commits from ~5 mid-sized, well-tested Python repos
- Revert the fix to create a "buggy PR", labeled with the file and line range of the bug
- Include clean PRs with no known bug to measure false positives
- Target: 150–300 cases

**Splits** ([[ADR-007 dev-holdout benchmark split]])
- **dev**: for tuning
- **holdout**: run only at milestones

**Leakage risk:** prefer commits after model training cutoffs, or less famous repos.

**Planned code location:** `evals/benchmark/` (`mine_commits.py`, `build_cases.py`, `data/dev` and `data/holdout` as JSONL).

Consumed by the [[Eval Harness]]. Risks: [[Label Noise]], [[Eval Cost]].
