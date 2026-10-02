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
  - "[[ADR-023 Arithmetic-or-numeric logic category]]"
  - "[[Glossary]]"
---

# Benchmark

**Purpose:** a labeled set of PRs to measure review quality against.

## Construction
- Mine bug-fix commits from **five repos** (Q20, decided 2026-10-02): `pallets/click`, `agronholm/anyio`, `fastapi/fastapi`, `marshmallow-code/marshmallow`, `Textualize/rich`. `encode/httpx` and `encode/httpcore` are dropped.
  - **Why five:** the ≥40-commit bar was a per-repo viability heuristic; what matters is total case count and category diversity. On three repos, anyio's concurrency-heavy set would dominate overall recall. Marshmallow and rich add parsing/serialisation, rendering and type/contract cases (estimate before Step 3: ~195 buggy, ~280 total with clean).
- Revert the fix to create a "buggy PR", labeled with the file and line range of the bug
- Label each case with its category: logic-bug taxonomy ([[ADR-019 Logic bug taxonomy]]) or CWE Top 25 ID ([[ADR-022 CWE Top 25 security taxonomy]])
- Include clean PRs with no known bug to measure false positives
- Target: 150–300 cases
- **Category coverage is uneven.** Per-category recall is always reported with raw counts (e.g. `3/7`), never as bare percentages, and both micro and macro recall are reported ([[Metrics]])
- **Security coverage is too thin to measure:** a keyword pass found ~6 security-related candidates across all repos, so most of the 11 CWE categories will have 0–1 cases. M3 reports security recall with raw counts and states in every report that it is not statistically meaningful. A dedicated security case set is Q58 (target M6)

## Repo selection criteria
- Actively maintained, well-tested Python projects with clear bug-fix commit conventions
- Mid-popularity preferred over famous repos, to reduce memorisation risk
- Target shapes: a web framework/library, a data tool, a CLI tool, a parsing/serialisation library, a smaller async library
- Commit window 2025-04-01 → 2026-10-01 (18 months), preferring commits after mid-2025. No single training cutoff applies, since the cascade uses four different models; each case records its commit date so results can be split by it ([[Benchmark Leakage]])
- Verification table below; repo choice decided by the owner (Q20, closed 2026-10-02).

## Case construction rules (Q56, decided 2026-10-02)
1. **Size filter counts package source only.** The ≤3 files / ≤60 changed lines limit counts only `.py` files in the package directory; tests, docs, changelogs and CI files are excluded from the count.
2. **Revert package source only.** The buggy PR reverts only the package source changes of the fix commit, never test files, changelog entries or docs. Reverting them would delete a test named after the bug and a "Fixed …" line, handing the reviewer the answer and inflating recall.
3. **Category labels** follow the precedence rules in the [[Glossary]] ([[ADR-023 Arithmetic-or-numeric logic category]]); unclear cases stay unlabeled (null) and count only toward location-only recall.

## Built cases (M3 Steps 2–3, rebuilt 2026-10-03 with the SZZ clean rule)
Built by `evals.benchmark.mine_commits` then `evals.benchmark.build_cases` (reports: `evals/benchmark/data/mining_report.json`, `build_report.json`). **238 cases: 168 buggy + 70 clean (29% clean); dev 143 / holdout 95.**

| Repo | Buggy dev / holdout | Clean dev / holdout |
|---|---|---|
| pallets/click | 25 / 17 | 10 / 6 |
| agronholm/anyio | 33 / 21 | 8 / 6 |
| fastapi/fastapi | 25 / 15 | 11 / 8 |
| marshmallow-code/marshmallow | 9 / 7 | 2 / 2 |
| Textualize/rich | 10 / 6 | 10 / 7 |

| Changed lines | Buggy | Clean | Clean target |
|---|---|---|---|
| 1-5 | 60 | 26 | 26 |
| 6-15 | 51 | 22 | 22 |
| 16-30 | 33 | 14 | 14 |
| 31-60 | 24 | 8 | 10 |
| **Median** | **11** | **10** | |

- 12 buggy candidates discarded as non-behavioural (6 annotation-only, 5 whitespace/comment/docstring, 1 rename); 24 clean candidates likewise. Clean shortfall: only the 31–60 bucket (8 of 10).
- **Ranges per buggy case** (count of cases): 1: 55 | 2: 38 | 3: 32 | 4: 14 | 5: 9 | 6: 6 | 7: 5 | 8: 3 | 10: 2 | 12: 1 | 13: 1 | 14: 1 | 23: 1. A hit on any range is *lenient* recall; *strict* recall uses the human-marked primary range ([[Metrics]]).
- Heuristic category labels: 102 of 168 buggy cases have none; human labels replace them (below).
- Commit-message trailers naming co-authors or assistants (`Co-authored-by:`, `Assisted-by:`) are stripped when mining.

## Clean PRs (Q60, decided 2026-10-03)
A clean case is a non-fix commit **none of whose added or modified lines was changed by a later bug-fix commit within 6 months**. This uses the approach of the **SZZ algorithm** (Śliwerski, Zimmermann and Zeller, "When do changes induce fixes?", MSR 2005): for each bug-fix commit, `git blame` its removed lines at its parent to find the commits that introduced them; a blamed commit is not clean. Implemented in `evals/benchmark/szz.py`. (It replaced an earlier per-file rule that left only 25 clean cases, because these libraries' core files receive fixes constantly.)
- Clean candidates pass the same filters as buggy ones: package source only, ≤3 files / ≤60 lines, the same subject filter, and a behavioural change (no cosmetic-only, typing-only or rename-only diffs).
- Sampled per size bucket to match the buggy distribution, ~30% clean overall; a bucket that is still short is accepted and reported.
- SZZ's known limits apply: a fix that only adds lines blames nothing, and a line changed again before the fix is attributed to the later change. **The rule is a heuristic, not proof** that a case is bug-free.
- The false-positive rate is always reported per size bucket, so a size shortcut is detectable ([[Metrics]]).

## Human labels (Q61, decided 2026-10-03)
- Category labels come from **human labelling**, not an LLM: LLM labels would make category-correct recall measure LLM-to-LLM agreement.
- Tool: `python -m evals.benchmark.label --split dev` (resumable; writes `evals/benchmark/data/labels_human.jsonl`). For each buggy case it records validity (or a drop reason: feature, typing-only, refactor, not-a-bug, other), the category, and the **primary range** (the actual bug); for clean cases, "looks clean" or "suspicious" with a note. The holdout split is refused unless `--freeze` is passed: holdout is labelled only after prompt tuning is frozen.
- **Splits are frozen.** Dropped cases are removed; no case ever moves between dev and holdout.
- Human labels override heuristic labels; heuristic labels are kept for comparison.
- **Label noise** = the fraction of dev cases the owner drops, reported with the count ([[Label Noise]]).
- **Single-annotator limitation:** one person labels every case; there is no inter-annotator agreement measure.
- Until the holdout is labelled: location recall uses all cases; category-correct recall uses human-labelled cases only.

## Splits ([[ADR-007 dev-holdout benchmark split]])
- **60% dev** (for tuning) / **40% holdout** (run only at milestones)
- Stratified by repo and bug category, so both splits carry the same mix
- The holdout is larger than typical ML practice because the total case count is small and holdout numbers must be statistically meaningful
- The precision filter trains on dev-split findings only ([[ADR-017 Dev-split-only training data for the precision filter]])
- Outcome labels from benchmark repos must not leak into holdout ([[ADR-011 Finding outcomes as precision-filter labels]])

**Code location:** `evals/benchmark/`. Built: `verify_repos.py` (Step 1). Planned: `mine_commits.py`, `build_cases.py`, `data/dev.jsonl` and `data/holdout.jsonl`.

Consumed by the [[Eval Harness]]. Risks: [[Benchmark Leakage]], [[Label Noise]], [[Eval Cost]].

## Repo verification (Q20, M3 Step 1, 2026-10-01): decided, five repos
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
