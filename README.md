# Themis

> An AI code reviewer that weighs the evidence before it speaks.

Themis is a GitHub App that automatically reviews pull requests, paired with a reliability layer that measures review quality and blocks changes that make it worse. The core promise is trustworthy judgment: high precision, low noise, and every design decision backed by benchmark numbers.

## Status

| Milestone | What it delivers | State |
|---|---|---|
| M1 | Skeleton: webhook, queue, worker, storage, tracing | Built |
| M2 | Baseline reviewer: one LLM pass over the diff, findings posted as PR comments | Built; verified on a live PR (2026-10-01) |
| M3 | Benchmark, eval harness, metrics, dev baseline | Built; dev baseline measured (below) |
| M4 | Repo context: structural lookup plus hybrid search | Wired behind `CONTEXT_BUDGET` (off by default); the k = 3 ablation is running |
| M5 | Precision filter | In progress, trained from cached dev findings |
| M6 | Guardrails and prompt-injection set | Planned (week 2) |
| M7 | CI quality gate, no LLM calls in CI | Planned (week 2) |
| — | Holdout labelling, final holdout runs, results page | Planned (week 3) |

The plan and scope cuts are in [`ADR-030`](docs/vault/04%20Decisions/ADR-030%20v1%20finish%20plan%20and%20scope%20cuts.md) and the [Roadmap](docs/vault/07%20Progress/Roadmap.md).

## Dev baseline

All numbers are on the **dev split** (121 scored cases: 80 buggy, 41 clean), with the pinned eval model `groq/openai/gpt-oss-120b`. Intervals are 95% (Newcombe for J, Wilson elsewhere). Holdout numbers come only at the end ([ADR-007](docs/vault/04%20Decisions/ADR-007%20dev-holdout%20benchmark%20split.md)).

| Metric | v1 | v1 rerun (identical) | v2 (current) | Chance baseline |
|---|---|---|---|---|
| Youden's J (detection − clean flag rate) | **0.435** (0.257 to 0.586) | 0.388 (0.219 to 0.543) | **0.327** (0.161 to 0.486) | 0.000 |
| Detection rate | 85.0% (68/80) | 90.0% (72/80) | 88.8% (71/80) | 100% |
| Strict category-correct recall | 51.2% (41/80) | 45.0% (36/80) | 51.2% (41/80) | 42.5% (34/80) |
| Precision | 68.5% (74/108) | 63.2% (74/117) | 66.9% (83/124) | 38.7% |
| Clean flag rate | 41.5% (17/41) | 51.2% (21/41) | 56.1% (23/41) | 100% |

**Key caveats:**
- **Runs are not reproducible.** At temperature 0 the provider still serves each call from a different backend build. The v1 rerun, with identical code and prompts, changed 19 of 80 category-correct outcomes and 12 of 41 clean flags. v1 → v2 is within that noise on every measure. From now on, every configuration is measured as the **mean of k = 3 runs** (below), and these single runs are directional only.
- **The chance baseline matters.** A reviewer that flags the first changed line of every hunk gets J = 0 but 100% detection, so detection alone says nothing; J, category-correct recall and the clean flag rate carry the signal.
- **Clean cases are a heuristic.** 3 of 41 dev clean cases look suspicious on inspection, so up to 7.3% of the clean flag rate may be label noise.
- **Small benchmark.** With 80 buggy cases, an improvement needs about 11 net category-correct fixes (at k = 3) to be detectable.
- **Below the v1 targets.** J ≥ 0.60, clean flag rate ≤ 20%, precision ≥ 80%. M4 (context) and M5 (precision filter) are the planned improvements.

Full reports: [`docs/vault/08 Results/`](docs/vault/08%20Results/).

## Methodology

**Benchmark.**
- **Five Python repositories:** `pallets/click`, `agronholm/anyio`, `fastapi/fastapi`, `marshmallow-code/marshmallow`, `Textualize/rich`.
- **Commit window:** 2025-04-01 → 2026-10-01, non-merge commits on the default branch.
- **Buggy cases** are real bug fixes, reverted. The reverted fix becomes the "PR" to review, and the labelled bug location is what the fix changed.
- **Revert package source only:** the buggy PR reverts only the fix's package `.py` changes, never its tests, changelog or docs, which would hand the reviewer the answer.
- **Size limit:** ≤ 3 files and ≤ 60 changed lines of package source.
- **Clean cases** are non-fix commits none of whose changed lines were touched by a later bug fix within 6 months. They are identified with the approach of the SZZ algorithm (Śliwerski, Zimmermann and Zeller, "When do changes induce fixes?", MSR 2005): blame each fix's removed lines to find the commits that introduced them. Clean cases are size-matched to the buggy ones. SZZ is a heuristic: a fix that only adds lines blames nothing.
- **Splits:** 238 cases, split 60/40 into dev (143) and holdout (95), stratified by repo and frozen.

**Labels.**
- **Labelling:** the dev labels were assigned by an LLM from human-written upstream evidence: each fix's PR and issue threads, read-only. Recorded per case: valid or dropped (feature, typing-only, refactor, not a bug), the category from a fixed taxonomy (seven logic categories plus a CWE Top 25 security subset), and the bug-holding line ranges.
- **Kept:** 80 of 102 buggy dev cases.
- **Verification:** the owner checked a stratified sample of 25 kept cases plus 3 borderline ones and agreed on validity, category and primary range in 25 of 25 (95% Wilson lower bound 86.7%).
- **Holdout:** labelled only after prompt tuning is frozen.

**Eval setup.**
- **Neutral title:** every case gets the same PR title ("Proposed change"); the real commit subject would name the bug.
- **Issue references masked:** issue and PR references in removed lines are masked.
- **Pinned model:** eval runs use one pinned provider and model, never the production fallback cascade ([ADR-024](docs/vault/04%20Decisions/ADR-024%20Eval%20runs%20pin%20a%20single%20provider%20and%20model.md)).
- **Run fingerprint:** each run records a hash of the review-path code and of every rendered prompt, and refuses to resume after either changes.

**Metrics: detection first** ([ADR-025](docs/vault/04%20Decisions/ADR-025%20Detection-first%20metrics.md)).
- **Headline:** Youden's J = detection rate − clean flag rate. Detection means any finding on a buggy case; a clean flag means any finding on a clean case.
- **Also reported:** strict category-correct recall (a finding on a labelled bug-holding range, with the right category), precision, and the clean flag rate, all beside the chance baseline.
- **Why not location matching:** location within ±3 lines is reported only as a diagnostic, because 81% of a typical buggy diff's changed lines already lie inside the labelled ranges.

**Aggregated evaluation** ([ADR-029](docs/vault/04%20Decisions/ADR-029%20Aggregated%20evaluation.md)).
- **Why aggregate:** outputs are not reproducible on the provider, so each configuration is run **k = 3 times**.
- **Per-case outcomes** are means over the runs.
- **Comparisons** use a paired permutation test on the per-case means, plus a bootstrap 95% CI on the difference, reported as net cases fixed.

## v1 scope
- Python repositories only
- Findings limited to logic bugs and security issues
- No style or formatting comments

## Limitations
- **Public repositories only.** Themis sends PR diffs, unmasked, to free-tier LLM providers and to Langfuse cloud for tracing. Some providers' free-tier terms permit using submitted data to improve their products (Google's Gemini API free tier states this). Do not install Themis on private repositories.
- **No secret masking.** Masking is required before any private-repo support, and is not part of v1.
- **Large PRs are truncated.** A diff longer than 100,000 characters is cut at that length and only the first part is reviewed. Chunking or per-file review is not built in v1 (Q48).
- **Repository context needs a recognisable package layout.** With `CONTEXT_BUDGET` above 0, context comes from a top-level `pkg/` or `src/pkg/` package of at most 2,000 files; other layouts are reviewed on the diff alone.
- **Security recall is not measured meaningfully.** The benchmark has too few security cases; a dedicated security benchmark track (Q58) is deferred to after v1.

## Training data rule
The precision filter is trained **only on findings generated from dev-split benchmark cases, never holdout**. `training/build_training_set.py` enforces this by rejecting any case ID present in the holdout split. Holdout numbers are only meaningful if the holdout never touches training.

## Documentation
- [`docs/vault/`](docs/vault/): the project knowledge vault (Obsidian). Start at [`00 Index.md`](docs/vault/00%20Index.md).
- [`docs/flow.md`](docs/flow.md): what the code actually does at runtime.
- [`docs/decision.md`](docs/decision.md): why each change was made.
- [`scripts/check_vault.py`](scripts/check_vault.py): run in CI; fails the build when the vault, `docs/flow.md` and the code drift apart.
