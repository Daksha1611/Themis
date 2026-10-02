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
