---
name: Session Log
description: "Dated log of every working session: done, next, blockers."
type: progress
status: in-progress
tags: [progress]
related:
  - "[[Current Status]]"
  - "[[Open Questions]]"
---

# Session Log

## 2026-09-28
**Done:** created the git repo, the knowledge vault (`docs/vault/`), `docs/decision.md`, and `docs/flow.md` from the approved spec. No application code.
**Next:** approval of the planning docs; resolve [[Open Questions]].
**Blockers / questions:** see [[Open Questions]].

## 2026-09-28 (2)
**Done:** planning docs approved. Added the [[Themis Map.canvas|Themis Map]] canvas (data-flow map of every component and reliability note), graph view colour groups by folder (local setting), and the [[Prior Art]] note comparing Themis with a course PR-reviewer project.
**Next:** resolve [[Open Questions]], including proposals 34–36.
**Blockers / questions:** none new beyond Open Questions.

## 2026-09-28 (3)
**Done:** accepted prior-art proposals 34–36 as ADR-009 (OWASP Top 10 security taxonomy), ADR-010 (Prometheus + Grafana operational metrics), ADR-011 (finding outcomes as precision-filter labels). Added [[Operational Monitoring]], [[Prometheus]], [[Grafana]]; updated affected component, reliability, risk, and map notes.
**Next:** resolve [[Open Questions]] 1–33 and 37–43.
**Blockers / questions:** new questions 37–43.

## 2026-09-29
**Done:** recorded the answers to Open Questions 1–43. Added ADR-012 to ADR-019, [[GitHub Integration]], [[Benchmark Leakage]], and stack notes for SQLAlchemy, Alembic, sentence-transformers, ruff, mypy, pytest, pytest-cov, and Caddy. Rewrote ADR-011 as a pilot. Switched ADR frontmatter to `status: accepted`. Added a root README with the dev-split-only training rule. Settled four conflicts first: results page deploys via GitHub Actions (not served from `docs/`); rule goes in a new root README; SQLAlchemy covered by ADR-012; CI and drift use a separate eval database.
**Next:** decide Q37 and Q41; choose benchmark repos (Q20).
**Blockers / questions:** Q20, Q25, Q37, Q41 open.

## 2026-09-29 (2)
**Done:** recorded five benchmark repo candidates, two fallbacks, and the verification rule in [[Benchmark]] (corrected `python-trio/anyio` to `agronholm/anyio`). Added the Open Reconsideration section to ADR-009 and raised Q37b. Superseded ADR-010 for v1; Prometheus and Grafana moved to post-v1 stretch goals; closed Q40 and Q41. Confirmed ADR-012 already covers SQLAlchemy. `docs/flow.md` unchanged (never described Prometheus).
**Next:** verify the repo candidates (Q20); decide Q37b.
**Blockers / questions:** Q20, Q25, Q37b open.

## 2026-09-29 (3): Milestone 1
**Done:** built the M1 skeleton: webhook with HMAC verification and event filtering, arq enqueue, worker that gets an installation token, posts "⚖️ Themis is reviewing this PR." and writes a `review_runs` row, Langfuse traces and spans, Docker Compose (five services, root `compose.yaml` includes `infra/`), CI workflow. Added [[ADR-020 M1 runtime dependencies]] (httpx, PyJWT, pydantic-settings, uvicorn, psycopg). Recorded installed versions in the stack notes. Renamed `ReviewResult.model_config` to `llm_config`. Local checks: 13 tests pass, ruff and mypy clean; compose smoke test returned 202 / 403 / 200-ignored as specified, the worker picked up the job and failed at GitHub with 401 as expected without a real App.
**Next:** register the GitHub App and Langfuse keys and re-run the live checks; M2 (baseline LLM reviewer, Alembic init).
**Blockers / questions:** Q44 (Alembic deferred), Q45 (GitHub App credentials), Q46 (Langfuse credentials).

## 2026-09-30: Milestone 2
**Done:** installed the Langfuse agent skill (user-level) and followed it for tracing. Wrote the GitHub App key into `.env` and verified every credential against its service. Step 0: removed the bootstrap, initialised Alembic, verified revision 1 on a fresh database and stamped the dev database; revision 2 adds the M2 columns. Built the LLM client, final Finding/ReviewResult schema, diff fetch, baseline pass, PR review posting, and the new worker flow. 38 tests pass; ruff and mypy clean. Live run on `Daksha1611/themis-test-repo` PR #1: webhook → worker → real token → diff fetch 403 (missing Contents permission) → real error comment → `failed` row → full trace in Langfuse. Trace audit fixes: root level reflects failure, service names set, deprecated `set_trace_io` removed.
**Next:** owner actions Q50–Q52, then rerun the live checks and close M2.
**Blockers / questions:** Q50 (App Contents permission), Q51 (OpenRouter limit), Q52 (tunnel).

## 2026-10-01: M2 provider cascade
**Done:** corrected the GitHub App permission set (Contents: Read-only) and closed Q50. Replaced the single OpenRouter model with a free-tier four-provider cascade ([[ADR-021 Free-tier four-provider LLM cascade]]): read LiteLLM 1.103.1's routing for each prefix, listed each provider's live models with the owner's keys, and test-called candidates. Chose `openai/gpt-oss-120b` (Groq), `gemini-3.5-flash` (Gemini; `gemini-2.5-flash` returned 404), `codestral-2508` (Mistral), `qwen/qwen3.8-27b:free` (OpenRouter). Added [[Free Tier Throughput]], Groq/Gemini/Mistral stack notes. Fixed a LiteLLM cost-lookup bug for slash-containing model IDs and added file-path normalisation. 46 tests pass; ruff and mypy clean. Closed Q51.
**Next:** owner fixes the clock (Q53) and tunnel (Q52); rerun the live test; close M2.
**Blockers / questions:** Q53 (clock 5 h 22 min fast: GitHub returns 401 for the App JWT), Q52 (tunnel 0 ready connections).

## 2026-10-01 (2): M2 live verification
**Done:** owner fixed the clock (Q53) and restarted the tunnel. Verified all five preconditions (UTC time, `/health` through the tunnel, App JWT, installation token, diff fetch with Contents: Read). Live test: GitHub delivered both PR events through the tunnel; PR #2 (planted bugs) got 3 accurate line comments; PR #3 (clean) got the no-issues comment; both answered by Groq `openai/gpt-oss-120b`; both traces complete in Langfuse with provider, tokens and cost; two `review_runs` rows with non-zero `prompt_tokens`. Trace audit: model thinking was missing; fixed (Groq exposes it as `reasoning`, and metadata truncates, so it now sits in the generation output). M2 closed.
**Next:** Q54 (categories in the prompt), then M3.
**Blockers / questions:** none blocking. Q54 must be fixed before M3 measures recall.

## 2026-10-01 (3): M3 pre-work and Step 1
**Done:** Q37b decided: CWE Top 25 (2024 edition, verified against MITRE's CWE view 1430; a 2025 edition exists but drops CWE-798 and CWE-400), Python-reachable subset of 11 + `security-other` ([[ADR-022 CWE Top 25 security taxonomy]]); ADR-009 superseded. Q54 fixed: categories listed in the prompt, validated in `Finding`; live check on the three test PRs returned only taxonomy categories (CWE-89, CWE-22, resource-leak, off-by-one-or-boundary, null-or-none-handling, error-handling). Test repo cleaned. Step 1: `evals/benchmark/verify_repos.py`; viable: click (65), anyio (67), fastapi fallback (58); not viable: httpx (0), marshmallow (26), rich (24), httpcore (2).
**Next:** owner approves the repo list and size-filter scope; then Steps 2–8.
**Blockers / questions:** Q20 (repo list), Q55 (arithmetic category), Q56 (size-filter scope).

## 2026-10-02: Vault audit and hardening
**Done:** owner approved the audit report (all nine recommendations). Fixed every finding: `name`/`description` frontmatter on all notes; per-type `status` meanings in the [[Glossary]] and corrected statuses; Docker.md frontmatter repaired; ADR-005 marked amended by ADR-021 and ADR-004 refined by ADR-015; component notes split into built versus planned; Storage, Eval Harness and the Architecture Overview agree on where eval results go (Q57); metric definitions completed; [[Open Questions]] reformatted with unique numbers (Q20, Q25, Q37 duplicates removed) and M3 blockers marked; Q49 decided for public diffs; canvas gained the two missing risks; `docs/flow.md` call graph covers every function in `app/`; README status corrected. Added [[00 Brief]], [[09 External Facts]] (re-verified live: three providers answered, OpenRouter 429; Groq and Mistral limits from headers; App permissions and a real diff fetch; library versions; no 2026 CWE edition), stack notes [[starlette]] and [[pytest-asyncio]], `scripts/check_vault.py` with 21 tests and a `vault-check` CI job, and new local project rules (Brief first, verify before trusting, 30-day re-verification).
**Next:** owner decisions on Q20, Q56 and Q55, then M3 Step 2 (mining).
**Blockers / questions:** Q20, Q55, Q56. OpenRouter's free model was rate-limited upstream today; re-check before long M3 runs.

## 2026-10-02 (2): audit amendments reconciled
**Done:** a second session had applied the audit fixes from "continue", without the owner's amendments. Reconciled with the actual approval: empty `version:` only while planned (checker and 7 notes); eval output split into case-level `results.jsonl` and run-level summaries in the eval database for the M7 gate, and the Q57 entry created for it withdrawn (an earlier entry in this log mentions it); public repositories only (README Limitations, Brief, Q49 retitled to the masking work); Eval Cost rewritten as a request budget with mitigations shared with [[Free Tier Throughput]]; Benchmark says three repos and requires raw counts; Benchmark Leakage records the window-start effect, the required mined-commit date distribution and the results-page caveat rule; checker exemptions encoded as rules (migrations dir, private leaf helpers); [[09 External Facts]] lists all 19 pinned versions. `decision.md` pre-work entry restored to its original text; completion entry corrected; the `app/main.py` comment and the CI job logged separately.
**Next:** owner decides Q20, Q56 and Q55; then M3 Step 2.
**Blockers / questions:** Q20, Q55, Q56 (block M3).

## 2026-10-02 (3): M3 decisions and Steps 2–3
**Done:** committed and pushed the vault audit (CI green, including `vault-check`). Recorded the owner's decisions: Q20 five repos; Q55 `arithmetic-or-numeric` ([[ADR-023 Arithmetic-or-numeric logic category]]) with precedence rules shared by `app/taxonomy.py` (prompt), the [[Glossary]] and the labelling rules; Q56 package source only for size and revert. Added Q58 (security track, M6) and Q59 (regression-test validation). Step 2 mined 180 candidates; Step 3 built 168 buggy + 25 clean = 193 cases (dev 117, holdout 76), 15-case dev sample written. 107 tests pass; vault check passes.
**Next:** owner hand-checks `evals/benchmark/data/sample_for_review.md`; decides Q60 and Q61; then Steps 4–7.
**Blockers / questions:** Q60 (clean shortfall), Q61 (null labels), and the hand-check.

## 2026-10-03: Q60, Q61 and follow-ups
**Done:** committed and pushed Steps 2–3 (CI green). Recorded decisions: Q60 SZZ-style clean rule (70 clean cases, sizes matched; only the 31–60 bucket short, 8/10); Q61 human labels on dev with `evals/benchmark/label.py` (the 15-case sample file is replaced by the labelling pass); strict vs lenient recall, chance baseline, FP per size bucket, macro floor ≥5 ([[Metrics]]); ADR-023 clause for index and length arithmetic. Splits frozen: no existing case moved. Mining now strips `Co-authored-by:` / `Assisted-by:` trailers: upstream AI-assistant trailers had reached tracked data in the previous commit. 119 tests pass; vault check passes.
**Next:** owner labels dev cases; then Steps 4–7.
**Blockers / questions:** whether to rewrite history to remove the trailers from the earlier pushed commit (owner decision).

## 2026-10-03 (2): dev-split labels (M3 Step 3b)
**Done:**
- The owner could not hand-label the dev split, so the development assistant labelled all 143 dev cases (Q61 amended).
- Every judgement followed a reading of the case's upstream evidence: the PR, its conversation, review comments and reviews (bot comments included), and the linked issues. The evidence was fetched read-only (GET only, nothing posted upstream) by `evals/benchmark/fetch_evidence.py`. Three cases also needed the local upstream clones, and one needed its GitHub security advisory.
- Buggy: 80 of 102 kept, 22 dropped. Clean: 3 of 41 marked suspicious.
- Each kept case records its primary range and any contested ranges. Q62 is new: how strict recall treats contested ranges.
- Re-checked the first 8 cases after the session break; no changes.
- `write_labels.py` and `label_report.py` added, with 9 tests (128 pass).
- Label report: [[label-report-dev-2026-10-03]]. [[Benchmark]], [[Metrics]], [[Label Noise]], [[Open Questions]] and the Results README updated.

**Next:** the owner reviews the label report; then Steps 4–7.
**Blockers / questions:** Q62 (strict recall with contested ranges) before Step 6.

## 2026-10-03 (3): Q62, verification sample, metric caveats
**Done:**
- Recorded the owner's decisions: Q62 closed with three recall tiers and the chance baseline on all three ([[Metrics]]); [[Metrics]] gains the clean-case noise floor and the per-category-counts rule for macro recall.
- The SZZ code-movement limit is recorded in [[Benchmark Leakage]].
- Built `evals/benchmark/verify_sample.py` and wrote `evals/benchmark/data/verification_sample.md`:
  - 25 kept dev cases, stratified: type-or-contract 6, control-flow 5, concurrency-or-async 4, error-handling 4, one per small category;
  - every repo covered;
  - the owner's 3 borderline cases added and scored separately.
- Found and fixed evidence noise: anyio's PR template names issue #123 as a changelog example, and 19 label records listed it as evidence. Only those evidence lists changed; no label did.
- 137 tests pass; vault check passes.

**Next:** the owner marks the sample and reports the verdicts; agreement rates go into [[Benchmark]] and the label report; then Steps 4–7.
**Blockers / questions:** the owner's verdicts gate Steps 4–7.

## 2026-10-03 (4): owner verification recorded
**Done:**
- The verdicts are the owner's, given after reviewing all 28 sample cases: agree on every field. The agent entered the ticks at the owner's instruction.
- Score: 25/25 on validity, category and primary range (95% Wilson lower bound 86.7%); borderline cases 3/3.
- Recorded in [[Benchmark]], [[Label Noise]] and the label report (new section 9, [[label-report-dev-2026-10-03]]). 138 tests pass.

**Next:** M3 Steps 4–7.
**Blockers / questions:** none.

## 2026-10-03 (5): M3 Steps 4–6 built; stopped at the dry run
**Done:**
- Verification-file wording fixed: the verdicts are the owner's; the agent entered the ticks.
- [[ADR-024 Eval runs pin a single provider and model]] written and implemented (`PinnedLLM`; the worker still uses the cascade).
- Response cache, runner and metrics built, with 36 tests (174 pass). `docs/flow.md` section 9 and the call graph written.
- Every eval case gets a neutral PR title, because the real commit subject would reveal the bug.
- Dry run: 121 cases, prompts 125,635 tokens (63% of the daily budget), largest request 3,751.
- Past `gpt-oss-120b` completions in Langfuse average ~822 tokens, so the run is expected to need about two days. Per the brief, no LLM call was made.

**Next:** owner decides Q64; then Step 7 (`evals/report.py`, baseline run, cache-only rerun).
**Blockers / questions:** Q64.

## 2026-10-03 (6): dev baseline run (M3 Step 7)
**Done:**
- Q64 closed: two-day plan, shuffled order with a recorded seed, sessions and per-case timestamps, model-consistency check, leak scan (9/80 buggy and 2/41 clean diffs flagged; nothing changed). The neutral PR title is recorded as a known difference between eval and production.
- Groq's model list was checked live before the run.
- The run finished in one session: ~1 hour, 122 provider calls, 219,611 tokens, no daily-limit response.
- Cache-only rerun: identical metrics, 0 provider calls.
- `evals/report.py` written; report [[baseline-dev-2026-10-03]]. 179 tests pass.
- **Finding:** the chance baseline's location recall (strict 95%) beats the reviewer's (80%).

**Next:** metric redesign and leak masking (owner brief, 2026-10-04).
**Blockers / questions:** none.

## 2026-10-04: metric redesign, masking, diagnostics
**Done:**
- Outstanding Step 7 docs written. Groq's documented daily limit did not bind (219,611 tokens in one session); External Facts updated.
- Diagnostics:
  - base rate 81.2%, so location is non-discriminating;
  - miss breakdown;
  - coordinate check: no systematic offset, but an old-side convention gap (Q65).
- [[ADR-025 Detection-first metrics]] and McNemar written and tested against known values (Newcombe's worked example for the J interval).
- Masking rule `mask-issue-refs-v1`: 7 cases changed and rerun with exactly 7 LLM calls. Leak cases were not advantaged; McNemar p = 1.0.
- Clean-FP pattern recorded.
- New report [[baseline-dev-2026-10-04]]; [[baseline-dev-2026-10-03]] kept as superseded. 188 tests pass.

**Next:** owner decisions on Q65 and Q25; M4 not started.
**Blockers / questions:** Q65.

## 2026-10-04 (2): Q63, ADR-026, fingerprint, M4 groundwork
**Done:**
- Q63 noise floor measured and verified valid.
- ADR-026 built (numbered diff, line rule, line validation, one retry). Baseline v2 stopped at 6/121 on the Groq daily limit (200K rolling; confirmed).
- Two-hash run fingerprint with a recorded case order; v2 backfilled from `4feea8e` and checked after every commit.
- Q25 targets, sensitivity line and v1→v2 attribution in the report code.
- M4 groundwork:
  - [[ADR-027 Eval-time repo context]];
  - `app/context/` (tree-sitter chunker, cached MiniLM embeddings, Qdrant hybrid with an IDF sparse modifier and RRF, retriever), standalone, with a test that the review path never imports it;
  - stack notes for [[torch]], [[qdrant-client]] and [[tree-sitter-python]];
  - CI installs CPU-only torch.
- Retrieval eval [[context-retrieval-dev-2026-10-04]]: recall 21–25%, no leakage. 210 tests pass.

**Next:** resume v2 (2026-10-05, after ~14:10 UTC); the v2 report; the owner decides on a symbol-aware retrieval step.
**Blockers / questions:** Groq's daily window; retrieval design.

## 2026-10-05: ADR-028 structural lookup; M4 ablation plan
**Done:**
- [[ADR-028 Structural lookup plus hybrid search]] (amends ADR-015): definitions of referenced names, then callers of changed functions, then hybrid search. `app/context/structure.py`; `RelatedChunk` gains `source`, `via` and `ambiguous`.
- Re-evaluation [[context-retrieval-dev-2026-10-05]], no LLM calls:
  - resolution coverage 57–64% (was 21–25%);
  - caller coverage 39–73%;
  - composition at 1K: definitions 9%, callers 40%, semantic 49%;
  - 0 leakage.
- M4 ablation plan and falsification prediction recorded before any run.
- Context-aware dry run: 1K = 1.89 days of quota, 2K = 2.53, 4K = 3.80 (and over the per-request ceiling for 23 cases); default 1K.
- v2 fingerprint unchanged after every commit. 212 tests pass.

**Next:** resume v2; the v2 report; then the v2 + context ablation at 1K.
**Blockers / questions:** Groq's daily window.

## 2026-10-06: baseline v2 complete
**Done:**
- v2 finished: sessions on 2026-10-04 (6 cases, daily limit), 2026-10-06 04:45 (93 cases, session ended without a stop record) and 06:22 (22 cases). The fingerprint matched each time.
- Report [[baseline-dev-2026-10-06-v2]]: v1 → v2 McNemar detection b = 2, c = 5, p = 0.453; category-correct b = 8, c = 8, p = 1.000; clean flags b = 2, c = 8, p = 0.109. None significant, all within the noise floor.
- Attribution of the 30 changed cases: 4 retry-related, 2 numbering-related, 24 neither (noise).

**Next:** the M4 ablation (v2 + context at 1K) as the next row.
**Blockers / questions:** none.
