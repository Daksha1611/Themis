---
name: Benchmark
description: "Labeled benchmark of reverted bug-fix PRs and clean PRs: construction, splits, repo verification."
type: reliability
status: in-progress
tags: [reliability]
related:
  - "[[Eval Harness]]"
  - "[[Metrics]]"
  - "[[ADR-007 dev-holdout benchmark split]]"
  - "[[ADR-022 CWE Top 25 security taxonomy]]"
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
- Mine bug-fix commits from **three** repos: the three that passed verification (`pallets/click`, `agronholm/anyio`, `fastapi/fastapi`). Five candidates and two fallbacks were verified; final confirmation is Q20 (see Repo verification below)
- Revert the fix to create a "buggy PR", labeled with the file and line range of the bug
- Label each case with its category: logic-bug taxonomy ([[ADR-019 Logic bug taxonomy]]) or CWE Top 25 ID ([[ADR-022 CWE Top 25 security taxonomy]])
- Include clean PRs with no known bug to measure false positives
- Target: 150–300 cases
- **Three repos means thin category coverage.** Per-category recall must always be reported with raw counts (e.g. `3/7`), never as bare percentages ([[Metrics]])

## Repo selection criteria
- Actively maintained, well-tested Python projects with clear bug-fix commit conventions
- Mid-popularity preferred over famous repos, to reduce memorisation risk
- Target shapes: a web framework/library, a data tool, a CLI tool, a parsing/serialisation library, a smaller async library
- Commit window 2025-04-01 → 2026-10-01 (18 months), preferring commits after mid-2025. No single training cutoff applies, since the cascade uses four different models; each case records its commit date so results can be split by it ([[Benchmark Leakage]])
- The reasoning is recorded when repos are chosen. Verification done (table below); final confirmation pending (Q20).

## Clean PRs
Merged PRs from the same repos whose touched files had no bug-fix commit for the following 6–12 months. **This is a heuristic, not proof** that a PR is bug-free. The size distribution of clean PRs matches the buggy ones, so the reviewer cannot learn "big diff means bug".

## Splits ([[ADR-007 dev-holdout benchmark split]])
- **60% dev** (for tuning) / **40% holdout** (run only at milestones)
- Stratified by repo and bug category, so both splits carry the same mix
- The holdout is larger than typical ML practice because the total case count is small and holdout numbers must be statistically meaningful
- The precision filter trains on dev-split findings only ([[ADR-017 Dev-split-only training data for the precision filter]])
- Outcome labels from benchmark repos must not leak into holdout ([[ADR-011 Finding outcomes as precision-filter labels]])

**Code location:** `evals/benchmark/`. Built: `verify_repos.py` (Step 1). Planned: `mine_commits.py`, `build_cases.py`, `data/dev.jsonl` and `data/holdout.jsonl`.

Consumed by the [[Eval Harness]]. Risks: [[Benchmark Leakage]], [[Label Noise]], [[Eval Cost]].

## Repo verification (Q20, M3 Step 1, 2026-10-01): pending owner decision
`python -m evals.benchmark.verify_repos --include-fallbacks` (raw data: `evals/benchmark/data/repo_verification.json`). Window 2025-04-01 → 2026-10-01 (18 months), non-merge commits on the default branch. **Package-scoped** = message matches a bug-fix pattern and every non-test, non-doc, non-CI file touched is `.py` under the package directory. Viable = ≥40 package-scoped.

| Repo | Commits | Bug-fix msgs | Package-scoped | Package-only | Issue link | After 2025-07-01 | "Fixed" section | Viable | Est. after Step 2 filters* |
|---|---|---|---|---|---|---|---|---|---|
| encode/httpx | 17 | 2 | 0 | 0 | 0 | 0 | yes | ❌ | 0 |
| pallets/click | 446 | 109 | 65 | 15 | 22 | 59 (90%) | no | ✅ | 49 |
| marshmallow-code/marshmallow | 144 | 31 | 26 | 5 | 1 | 24 (92%) | yes | ❌ | 18 |
| Textualize/rich | 196 | 31 | 24 | 12 | 3 | 16 (66%) | yes | ❌ | 21 |
| agronholm/anyio | 318 | 96 | 67 | 4 | 27 | 62 (92%) | no | ✅ | 58 |
| encode/httpcore (fallback) | 7 | 3 | 2 | 1 | 0 | 1 (50%) | yes | ❌ | 2 |
| fastapi/fastapi (fallback) | 2046 | 128 | 58 | 10 | 0 | 55 (94%) | no | ✅ | 49 |

\* Rough estimate: package-source changes ≤3 files and ≤60 lines, subject line not refactor/typo/docs/bump. Counting test and changelog files toward the limits roughly halves the yield (click 55 → 30).

- `encode/httpx` has almost no development in the window (17 commits); `encode/httpcore` likewise.
- `python-trio/anyio` (as listed in the brief) does not exist; `agronholm/anyio` was verified. `tiangolo/fastapi` is now `fastapi/fastapi`.

Shortlist for Q20. **Not final:** each repo must pass the verification rule below.

### 1. encode/httpx (shape: web/HTTP library)
- Clear `CHANGELOG.md` with a `Fixed:` section on every release
- Bug types: async edge cases, URL parsing, header handling, streaming
- Memorisation risk: low-medium (less famous than requests)
- Verify: filter commits containing "fix" in 2025–2026; check that 10 messages are specific enough to classify as bug-fix vs refactor

### 2. pallets/click (shape: CLI tool)
- Clean commit history, well-labeled issues, excellent test suite
- Bug types: argument parsing edge cases, help text, type coercion, context handling
- Memorisation risk: low
- Verify: same as above

### 3. marshmallow-code/marshmallow (shape: parsing/serialisation)
- CHANGELOG clearly separates bug fixes from features; consistently high test coverage
- Bug types: type coercion, nested schema edge cases, error handling, validation
- Memorisation risk: low
- Verify: same as above

### 4. Textualize/rich (shape: data/rendering tool)
- Very well tested, clear issue-linked commits
- Bug types: rendering logic, string handling, async output, markup edge cases
- Memorisation risk: low-medium
- Verify: same as above

### 5. agronholm/anyio (shape: async library)
- Small codebase, extremely well tested, precise and well-described fix commits
- Bug types: structured concurrency edge cases, cancellation, task group behaviour
- Memorisation risk: low
- Verify: same as above
- Note: originally listed as `python-trio/anyio`, which does not exist on GitHub. AnyIO lives at `agronholm/anyio`.

### Fallbacks (if a candidate fails verification)
- `encode/httpcore`: httpx's transport layer, less famous
- `fastapi/fastapi` (formerly `tiangolo/fastapi`): very active, clear fix labels, more famous

### Verification rule
Before finalising any repo, manually check that:
1. It has identifiable bug-fix commits in the 2025–2026 date range.
2. Commit messages are specific enough for `mine_commits.py` to classify reliably.
3. The repo's test suite covers the areas where bugs were fixed, so a revert produces a failing test.

Record the result of this check per repo here when the final selection is made.
