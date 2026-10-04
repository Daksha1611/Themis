# Themis code decision log

A running log of every code change in this repo. An entry is appended **before** the change is made. No entry, no change.

## Rules
- Append only. Never edit or delete a past entry.
- If a change spans multiple sessions, each session gets its own dated entry.
- If a change is reverted, add a new entry explaining the revert rather than deleting the original.
- If you are unsure whether a change needs an entry, it does.

## Entry format
```markdown
## [short title of the change]
**Date**: YYYY-MM-DD
**File(s) affected**: list every file being created, edited, or deleted

### What I am changing
### Why I am making this change
### Alternatives I considered
### Reasons I rejected each alternative
### Trade-offs I am accepting
### What could go wrong
### How this affects other components
```

---

## Create the project knowledge vault and planning documents
**Date**: 2026-09-28
**File(s) affected**:
- `docs/vault/00 Index.md` (created)
- `docs/vault/01 Project/`: Vision, Scope, Non-Goals, Success Metrics, Glossary (created)
- `docs/vault/02 Architecture/`: Architecture Overview, Webhook Service, Job Queue, Context Builder, Review Graph, Finding Schema, Precision Filter, Guardrails, LLM Client, Storage (created)
- `docs/vault/03 Reliability/`: Tracing, Benchmark, Eval Harness, Metrics, CI Quality Gate, Drift Monitoring, Ablation Table (created)
- `docs/vault/04 Decisions/`: ADR-001 to ADR-008 (created)
- `docs/vault/05 Stack/`: one note per technology, 15 notes (created)
- `docs/vault/06 Risks/`: Eval Cost, Label Noise, Hosting, Scope Creep (created)
- `docs/vault/07 Progress/`: Current Status, Session Log, Open Questions (created)
- `docs/vault/08 Results/README.md` (created)
- `docs/decision.md` (created)
- `docs/flow.md` (created)
- `.gitignore` (created)

### What I am changing
Adding planning documentation only: an Obsidian vault holding the approved spec, this decision log, and an execution-flow document with every section marked `[NOT YET BUILT]`. `.gitignore` excludes Obsidian's local `.obsidian/` config folder. No application code is added.

### Why I am making this change
The spec requires the vault, decision log, and flow document to exist before any application code, so that every later change has a source of truth to follow and a place to be recorded.

### Alternatives I considered
1. Keep the notes in the existing standalone Obsidian vault outside the repo (`../Themis/Themis`).
2. Write the spec as a single long document instead of linked notes.
3. Commit the `.obsidian/` folder so vault settings are shared.

### Reasons I rejected each alternative
1. The spec places the vault at `docs/vault/`, versioned with the code it describes.
2. One document cannot show dependencies in Obsidian's graph view, which the spec requires.
3. `.obsidian/` holds per-machine state and plugin data (including a local REST API key), which must not be published.

### Trade-offs I am accepting
Fifty-four small notes must be kept in sync by hand; renaming a note can break wikilinks. Worth it because the notes are the source of truth and the graph makes dependencies visible.

### What could go wrong
- Notes drift from the code as it is built.
- Frontmatter conventions differ from the spec's literal examples (see Open Questions 2–6) and may need to be changed.
- Unresolved Open Questions may be filled in ad hoc during implementation instead of being decided.

### How this affects other components
No component behavior changes. Every component note (Webhook Service, Job Queue, Context Builder, Review Graph, Finding Schema, Precision Filter, Guardrails, LLM Client, Storage) is created with `status: planned`.

---

## Add architecture canvas, graph view colors, and prior-art note
**Date**: 2026-09-28
**File(s) affected**:
- `docs/vault/Themis Map.canvas` (created)
- `docs/vault/01 Project/Prior Art.md` (created)
- `docs/vault/00 Index.md` (edited: links to the canvas and Prior Art)
- `docs/vault/07 Progress/Open Questions.md` (edited: proposals from prior art)
- `docs/vault/07 Progress/Current Status.md` (edited)
- `docs/vault/07 Progress/Session Log.md` (edited)
- `docs/vault/.obsidian/graph.json` (edited, local only, gitignored)

### What I am changing
Adding a visual reference map of the system as an Obsidian Canvas, colour groups for the graph view (by folder), and a note comparing Themis to a published course project (an AI GitHub PR reviewer). Ideas taken from that project are recorded as proposals in Open Questions, not added to the spec.

### Why I am making this change
Requested: "make graph in obsidian vault for reference" and permission to take inspiration from the course project. Project rules forbid adding features or technologies without a proposal, so inspiration is captured as proposals.

### Alternatives I considered
1. Only configure the built-in graph view.
2. Draw a second Mermaid diagram inside a note.
3. Adopt the course project's ideas directly into the spec.

### Reasons I rejected each alternative
1. The graph view shows every link equally and has no data-flow direction; kept only as a complement.
2. Architecture Overview already has a Mermaid diagram; the canvas adds clickable nodes that open the real notes.
3. Project rules require proposing new features/technologies before adopting them.

### Trade-offs I am accepting
The canvas is a hand-placed layout that must be updated when components change. Graph colours live in `.obsidian/`, which is gitignored, so they are local to this machine.

### What could go wrong
- The canvas drifts from the component notes if one is updated without the other.
- Renaming a note breaks its canvas file node.

### How this affects other components
No component behaviour changes. No component note is edited.

---

## Adopt prior-art proposals 34–36 into the spec
**Date**: 2026-09-28
**File(s) affected**:
- `docs/vault/04 Decisions/ADR-009 OWASP Top 10 security taxonomy.md` (created)
- `docs/vault/04 Decisions/ADR-010 Prometheus and Grafana operational metrics.md` (created)
- `docs/vault/04 Decisions/ADR-011 Finding outcomes as precision-filter labels.md` (created)
- `docs/vault/03 Reliability/Operational Monitoring.md` (created)
- `docs/vault/05 Stack/Prometheus.md`, `docs/vault/05 Stack/Grafana.md` (created)
- `docs/vault/02 Architecture/`: Architecture Overview, Finding Schema, Review Graph, Precision Filter, Storage (edited)
- `docs/vault/03 Reliability/`: Benchmark, Tracing (edited)
- `docs/vault/05 Stack/Docker.md` (edited)
- `docs/vault/06 Risks/Hosting.md` (edited)
- `docs/vault/01 Project/`: Glossary, Prior Art (edited)
- `docs/vault/00 Index.md`, `docs/vault/Themis Map.canvas` (edited)
- `docs/vault/07 Progress/`: Open Questions, Current Status, Session Log (edited)

### What I am changing
Adding three approved decisions to the spec: (1) security findings are categorised by OWASP Top 10; (2) Prometheus + Grafana monitor the running service (queue depth, job latency, error rates); (3) the outcomes of posted findings (resolved or dismissed on the PR) become training labels for the precision filter. Each gets an ADR, and every affected note is updated. Documentation only; no application code.

### Why I am making this change
Proposals 34–36 in Open Questions were approved. Project rules require an ADR before a new technology or pattern is used.

### Alternatives I considered
1. CWE IDs instead of OWASP Top 10 for the security taxonomy.
2. Leave operational metrics to Langfuse only.
3. Keep precision-filter labels coming only from offline labeling (`training/label_findings.py`).

### Reasons I rejected each alternative
1. CWE has hundreds of entries, far too fine-grained to label or measure on a 150–300-case benchmark.
2. Langfuse traces LLM calls, not service health (queue depth, worker errors, webhook failures).
3. Offline labels alone never improve from real usage; outcome labels add real-world signal. Offline labeling stays for the cold start.

### Trade-offs I am accepting
Two more services (Prometheus, Grafana) to run and host. OWASP Top 10 is revised every few years, so the version must be pinned. Outcome labels only exist after Themis is deployed and posting, and they are noisy (a dismissed finding is not always wrong).

### What could go wrong
- Monitoring work pulls time from the milestones (scope creep).
- Outcome signals are misread (e.g. a thread resolved without a fix counted as a true positive).
- Outcome labels from benchmark repos leak into the holdout split.
- Outcome learning drifts toward style preferences, which is a non-goal.

### How this affects other components
- **Finding Schema**: security findings gain an OWASP Top 10 category.
- **Review Graph**: the security pass classifies findings by OWASP Top 10.
- **Precision Filter**: training labels also come from finding outcomes.
- **Storage**: stores finding outcomes alongside review runs.
- **Job Queue / Webhook Service**: become subjects of operational monitoring (metrics exposure not yet designed).

---

## Record resolutions to Open Questions 1–43
**Date**: 2026-09-29
**File(s) affected**:
- Created: `README.md`; `docs/vault/02 Architecture/GitHub Integration.md`; `docs/vault/06 Risks/Benchmark Leakage.md`; `docs/vault/04 Decisions/` ADR-012 to ADR-019; `docs/vault/05 Stack/` Alembic, SQLAlchemy, sentence-transformers, ruff, mypy, pytest, pytest-cov, Caddy
- Edited: `docs/vault/00 Index.md`; `docs/vault/Themis Map.canvas`; `docs/vault/01 Project/` Glossary, Success Metrics; `docs/vault/02 Architecture/` Architecture Overview, Webhook Service, Job Queue, Context Builder, Review Graph, Finding Schema, Precision Filter, Guardrails, Storage; `docs/vault/03 Reliability/` Tracing, Benchmark, Eval Harness, Metrics, CI Quality Gate, Drift Monitoring, Ablation Table, Operational Monitoring; `docs/vault/04 Decisions/` ADR-001 to ADR-011 (status frontmatter), ADR-007, ADR-009, ADR-010, ADR-011 (content); `docs/vault/05 Stack/` Docker, Qdrant, PostgreSQL, Langfuse, GitHub Actions, HuggingFace Transformers, Pydantic; `docs/vault/06 Risks/` Eval Cost, Hosting; `docs/vault/07 Progress/` Open Questions, Current Status, Session Log; `docs/vault/08 Results/README.md`; `docs/flow.md`
- Not changed: the local project rules file (Q1: it never said "repo root", so no wording fix was needed)

### What I am changing
Recording the approved answers to Open Questions 1–43 in the vault: eight new ADRs (012–019), a GitHub Integration component, a Benchmark Leakage risk, eight stack notes, a root README stating the dev-split-only training rule, and updates to every affected note. `docs/flow.md` gets design references under its `[NOT YET BUILT]` sections. Documentation only; no application code.

### Why I am making this change
All open questions were answered and approved. Four conflicts or gaps were settled before editing: the results page deploys to GitHub Pages via an Actions build artifact (not by serving `docs/`, which holds the vault); the training rule goes in a new root README; SQLAlchemy is covered by ADR-012 with its own stack note; CI and drift runs use a separate eval database.

### Alternatives I considered
1. Serve GitHub Pages from `docs/` exactly as Q31 was worded.
2. Put the training rule only in ADR-017.
3. Leave SQLAlchemy as an unrecorded dependency of Alembic.
4. Have CI read and write the production database.

### Reasons I rejected each alternative
1. `docs/` already holds the vault and logs, which would all be published as the site.
2. The rule is the main safeguard of the holdout numbers and belongs where every reader sees it first.
3. Project rules forbid adding a technology without an ADR.
4. Chosen by the project owner: a separate eval database keeps CI and drift runs away from production data.

### Trade-offs I am accepting
The vault grows to 80+ notes, so keeping it in sync costs more. `docs/flow.md` gains design references before code exists; they are marked as not built so they cannot be mistaken for real behaviour.

### What could go wrong
- The flow.md design references drift from the vault if one is edited without the other.
- Order of steps after the graph is interpreted as: guardrail validation, then precision filter. Q7 says "post-graph" but does not order it against the filter.
- Q37 (security taxonomy) and Q41 (ADR-010) remain undecided; notes depending on them carry pending markers.

### How this affects other components
- **GitHub Integration** (new): owns App auth (JWT → installation token), diff fetching, review comment posting, and reading finding-outcome signals.
- **Webhook Service**: GitHub App auth moves to GitHub Integration; signature verification stays.
- **Job Queue**: orchestration order becomes context → guardrail sanitize → graph → guardrail validate → precision filter → comment posting.
- **Context Builder**: outputs a `ReviewContext`; indexes on install, incrementally per PR, and on manual command; local sentence-transformers embeddings; Qdrant native sparse vectors with RRF.
- **Guardrails**: runs twice (sanitize before the graph, validate after); never skips a review.
- **Review Graph**: receives sanitized `ReviewContext`; emits findings without confidence, using the logic-bug and security taxonomies.
- **Finding Schema**: adds severity enum, confidence 0.0–1.0 set by the filter, `security-other` with subcategory, `ReviewContext`, and `ReviewResult` fields.
- **Precision Filter**: sets confidence; threshold tuned by sweep; trained on dev-split findings only.
- **Storage**: `app/storage/` with SQLAlchemy and Alembic; raw outcome signals stored separately from derived labels.
- **LLM Client**: no change.

---

## Record benchmark repo candidates, supersede ADR-010, raise Q37b
**Date**: 2026-09-29
**File(s) affected**:
- `docs/vault/03 Reliability/Benchmark.md` (candidate repos section)
- `docs/vault/04 Decisions/ADR-009 OWASP Top 10 security taxonomy.md` (Open Reconsideration section)
- `docs/vault/04 Decisions/ADR-010 Prometheus and Grafana operational metrics.md` (status → superseded, rewritten)
- `docs/vault/03 Reliability/Operational Monitoring.md`, `docs/vault/03 Reliability/Tracing.md`
- `docs/vault/05 Stack/Prometheus.md`, `docs/vault/05 Stack/Grafana.md`, `docs/vault/05 Stack/Docker.md`
- `docs/vault/06 Risks/Hosting.md`
- `docs/vault/01 Project/Non-Goals.md`, `docs/vault/01 Project/Prior Art.md`
- `docs/vault/02 Architecture/Architecture Overview.md`, `docs/vault/Themis Map.canvas`
- `docs/vault/07 Progress/`: Open Questions, Current Status, Session Log
- Not changed: ADR-012 (already names SQLAlchemy explicitly; `05 Stack/SQLAlchemy.md` already exists); `docs/flow.md` (never described Prometheus or Grafana)

### What I am changing
Recording five benchmark repo candidates plus two fallbacks and the verification rule (Q20); adding the CWE Top 25 vs OWASP Top 10 reconsideration to ADR-009 and raising Q37b; superseding ADR-010 for v1 and moving Prometheus + Grafana to post-v1 stretch goals (closes Q40, Q41). Documentation only.

### Why I am making this change
Approved by the project owner this session.

### Alternatives I considered
1. Record `python-trio/anyio` exactly as given.
2. Delete the Operational Monitoring, Prometheus, and Grafana notes now that ADR-010 is superseded.
3. Rename ADR-012 to include SQLAlchemy.

### Reasons I rejected each alternative
1. That repository does not exist on GitHub; AnyIO lives at `agronholm/anyio`.
2. The ADR says "if reinstated", so the notes stay as the post-v1 record, marked deferred.
3. The rename was conditional on SQLAlchemy not being covered; ADR-012 already covers it.

### Trade-offs I am accepting
Deferred notes remain in the vault and graph, marked deferred, so they must not be mistaken for v1 scope. The status vocabulary has no "deferred" value, so those notes keep `planned` with a deferral banner.

### What could go wrong
- A candidate repo fails verification (low recent fix activity) and the fallbacks are also weak.
- Q37b stays unresolved and blocks the security pass node.

### How this affects other components
- **Webhook Service / Job Queue**: no longer expose operational metrics in v1.
- **Tracing**: Langfuse is the only v1 source of latency, cost, and token metrics.
- **Review Graph / Finding Schema**: unchanged; the security taxonomy stays OWASP Top 10 (2021) until Q37b is decided.
- **Benchmark**: gains a candidate list; no selection yet.

---

## M1 skeleton: webhook → queue → worker → dummy comment
**Date**: 2026-09-29
**File(s) affected**:
- Created (code): `app/__init__.py`, `app/main.py`, `app/config.py`, `app/schemas.py`, `app/llm.py`; `app/api/{__init__,webhook,health}.py`; `app/github/{__init__,auth,comments}.py`; `app/worker/{__init__,job,queue}.py`; `app/observability/{__init__,tracing}.py`; `app/storage/{__init__,models,repository}.py`, `app/storage/migrations/` (empty); `tests/{__init__,conftest,test_webhook,test_comments,test_queue}.py`
- Created (build/infra): `pyproject.toml`, `Dockerfile`, `compose.yaml`, `infra/docker-compose.yml`, `.env.example`, `.github/workflows/ci.yml`
- Edited: `.gitignore`, `docs/flow.md`
- Vault: `04 Decisions/ADR-020 M1 runtime dependencies.md` (created); `05 Stack/` httpx, PyJWT, pydantic-settings, uvicorn, psycopg (created); version fields in FastAPI, arq, Redis, Langfuse, Pydantic, Python, SQLAlchemy, ruff, mypy, pytest, pytest-cov, Docker, PostgreSQL, Qdrant; `02 Architecture/Finding Schema.md` (`model_config` → `llm_config`); `07 Progress/` Open Questions, Current Status, Session Log

### What I am changing
Building Milestone 1, the first application code:
- `POST /webhook` verifies the `X-Hub-Signature-256` HMAC with `hmac.compare_digest`, filters to `pull_request` `opened`/`synchronize`, builds a `ReviewJob`, enqueues it with arq, and returns 202.
- `GET /health` returns `{"status": "ok"}`.
- The arq worker's `handle_review_job` gets a GitHub App installation token, posts one issue comment ("⚖️ Themis is reviewing this PR."), and writes a `review_runs` row.
- Langfuse traces `webhook.received` and `review.job`, with spans for sub-steps.
- Docker Compose runs api, worker, redis, postgres, qdrant; CI runs ruff, mypy, pytest.

No diff fetching, LLM calls, Qdrant use, context building, or LangGraph.

### Why I am making this change
Milestone 1 brief from the project owner. It proves the end-to-end skeleton (GitHub → webhook → queue → worker → GitHub) before any review logic, and wires tracing from day one (ADR-006).

### Alternatives I considered
1. **Schema:** initialise Alembic now instead of a startup `CREATE TABLE IF NOT EXISTS`.
2. **HTTP client:** `requests` instead of httpx.
3. **Ignored events:** return 400 for non-PR events and unhandled actions instead of 200.
4. **Tracing:** trace at FastAPI middleware level instead of inside the webhook handler.
5. **Retryable GitHub errors:** raise arq's `Retry` directly from `app/github/comments.py`.
6. **Postgres driver:** asyncpg instead of psycopg 3.
7. **Compose location:** compose at the repo root only.

### Reasons I rejected each alternative
1. Alembic setup is non-trivial and not needed for a single dummy table; deferred to M2 pre-work. **Tech debt:** this temporarily departs from ADR-012 ("schema changes are made through Alembic migrations").
2. httpx supports async natively (FastAPI and arq are async); `requests` would block the event loop. Note: httpx was not in the vault stack before this session; ADR-020 adds it.
3. Per the project owner, GitHub treats non-2xx as failed deliveries; an event Themis deliberately ignores is not a failure.
4. Handler-level tracing can attach event metadata (event, action, repo, PR number) that middleware does not have without re-parsing the body, and keeps the trace scoped to webhook work only.
5. That would couple GitHub Integration to the queue library; comments.py raises its own `GitHubRetryableError` and the worker translates it into `arq.Retry`.
6. Chosen by the project owner.
7. The vault plans compose in `infra/`; a 3-line root `compose.yaml` includes it so plain `docker compose up` works.

### Trade-offs I am accepting
- Schema lives in a startup SQL statement until Alembic arrives in M2; a schema change before then means editing that SQL by hand.
- Exact version pins mean manual upgrades.
- Qdrant runs in Compose but is unused in M1.
- The installation-token cache is in-process memory, so each api/worker process fetches its own token.

### What could go wrong
- Signature verification bug lets forged webhooks through: covered by tests for valid, wrong, and missing signatures.
- Langfuse v4 and arq 0.28 APIs were read from the installed source; a future upgrade may break them (hence exact pins).
- Multi-line PEM keys in `.env` files are fragile; config accepts `\n`-escaped keys.
- The worker can start before the API creates the table; the worker also runs the `CREATE TABLE IF NOT EXISTS` on startup.
- No real GitHub App or Langfuse credentials exist yet, so the live path can only be verified up to the GitHub API call.

### How this affects other components
- **Webhook Service**: built (signature check, event filter, enqueue, 202, health).
- **Job Queue**: built (arq worker settings, `handle_review_job`), posting a dummy comment instead of running the review pipeline.
- **GitHub Integration**: App auth (JWT → installation token, 50-minute cache) and issue-comment posting built; diff fetch and line comments not yet.
- **Storage**: `review_runs` table and `create_run` / `update_run` built, without Alembic.
- **Finding Schema**: `Finding` and `ReviewResult` defined; `ReviewResult.model_config` renamed `llm_config` (Pydantic reserves `model_config`). `Finding.category` stays a plain string until Q37b settles the security taxonomy.
- **Tracing**: Langfuse client and trace/span helpers built.
- Context Builder, Review Graph, Precision Filter, Guardrails, LLM Client: untouched.

---

## M1 implementation deviations from the brief
**Date**: 2026-09-29
**File(s) affected**: `pyproject.toml`, `.dockerignore` (created), `infra/docker-compose.yml`, `app/worker/job.py`, `app/worker/queue.py`, `app/github/comments.py`, `app/api/webhook.py`, `app/observability/tracing.py`, `app/storage/repository.py`, `tests/test_queue.py`

### What I am changing
Recording changes made during M1 implementation that differ from the brief or were not in it:
1. `sqlalchemy[asyncio]` instead of `sqlalchemy`: SQLAlchemy 2.1 async needs greenlet (3.5.6), only installed via the extra.
2. `.dockerignore` added: without it `COPY . .` copies `.env` (secrets) and `.venv` into the image.
3. Healthchecks on redis and postgres, with `depends_on: condition: service_healthy`: without them the API starts before Postgres accepts connections and `ensure_schema` crashes it.
4. The `review_runs` row is written **inside** the `review.job` trace (as span `storage.create_run`) and the trace ends after it. The brief ended the trace before the DB write, which would leave the write untraced.
5. `post_review_comment` treats 429 + `Retry-After` like 403 + `Retry-After`. GitHub uses both for secondary rate limits.
6. A valid-signature `pull_request` event with invalid JSON or missing fields returns 400. The brief did not cover this case.
7. An extra `update_trace()` helper sets the trace metadata once the payload is parsed; the trace starts before verification, when only the event header is known.
8. The startup `CREATE TABLE` lives in `ensure_schema()` in `app/storage/repository.py`, not a separate script file, and the worker calls it too. A concurrent-create `IntegrityError` is logged and ignored.
9. The worker configures logging in `startup()`, otherwise app log lines are not shown under the arq CLI.
10. An extra test: `GitHubRetryableError` becomes `arq.Retry`.

### Why I am making this change
Each was needed for the brief's acceptance criteria to pass (1–3, 9), to keep tracing complete (4, 7), or to cover a case the brief left open (5, 6, 8, 10).

### Alternatives I considered
- Install greenlet as a separate pin instead of the extra.
- Retry-on-failure in the API's lifespan instead of Compose healthchecks.
- Keep the brief's order (end trace, then write the row).

### Reasons I rejected each alternative
- The extra is SQLAlchemy's documented way to get the right greenlet version.
- Healthchecks keep startup logic out of application code.
- A DB failure after the trace ends would be invisible in Langfuse.

### Trade-offs I am accepting
Slightly slower `docker compose up` (waits for healthchecks). 400 for malformed PR payloads is a non-2xx response to GitHub, but a malformed payload is a genuine failure, unlike an ignored event.

### What could go wrong
- `qdrant/qdrant:latest` is unpinned and can change under us.
- FastAPI's TestClient warns that using httpx with Starlette's test client is deprecated in favour of `httpx2`; tests pass today but may break on a future upgrade.

### How this affects other components
- **Job Queue**: trace now covers the DB write.
- **GitHub Integration**: 429 handled as retryable.
- **Webhook Service**: 400 for malformed PR payloads.
- **Storage**: schema bootstrap also runs from the worker.

---

## M2 baseline reviewer: pre-work
**Date**: 2026-09-30
**File(s) affected**:
- Created: `alembic.ini`; `app/storage/migrations/{env.py,script.py.mako,README}` and two revisions under `app/storage/migrations/versions/`; `app/github/client.py`; `app/github/diff.py`; `app/graph/__init__.py`; `app/graph/baseline.py`; `tests/test_baseline.py`, `tests/test_diff.py`, `tests/test_llm.py`, `tests/test_worker.py`
- Edited: `app/llm.py` (placeholder → client), `app/config.py`, `app/schemas.py`, `app/github/auth.py`, `app/github/comments.py`, `app/worker/job.py`, `app/worker/queue.py`, `app/main.py`, `app/storage/models.py`, `app/storage/repository.py`, `app/observability/tracing.py`, `app/api/webhook.py`, `infra/docker-compose.yml`, `pyproject.toml`, `.env.example`, `tests/conftest.py`, `tests/test_comments.py`
- Deleted: `tests/test_queue.py` (its M1 dummy-flow tests are replaced by `tests/test_worker.py`); `app/storage/migrations/.gitkeep`
- Docs and vault: `docs/flow.md`; `02 Architecture/` Finding Schema, LLM Client, Job Queue, GitHub Integration, Storage, Review Graph; `03 Reliability/Tracing.md`; `05 Stack/` Alembic, LiteLLM, OpenRouter, FastAPI, Langfuse; `07 Progress/` Open Questions, Current Status, Session Log

### What I am changing
1. **Step 0 (atomic):** remove the M1 `CREATE TABLE IF NOT EXISTS` bootstrap (`ensure_schema`) from the API and worker; initialise Alembic in `app/storage/migrations`; autogenerate revision 1 (`review_runs`, M1 columns) against an **empty scratch database** (the running M1 database already has the table, so autogenerating against it would produce an empty migration); verify it; `alembic stamp` the existing dev database to revision 1 once autogenerate shows no drift; run `alembic upgrade head` in the api and worker start commands. After the bootstrap removal, a fresh database without migrations has no table: intended.
2. **LLM client:** `complete()` in `app/llm.py` calls LiteLLM (`openrouter/<LLM_MODEL>`, `api_key=OPENROUTER_API_KEY`), returns `LLMResponse`, computes `cost_usd` with `litellm.completion_cost()`, and wraps failures in `LLMError(message, status_code)`.
3. **Schemas:** `Finding` becomes `file, line_start, line_end, category, subcategory, severity, message, suggestion, confidence, raw_llm_confidence`; adds `LLMConfig`, `TokenUsage`; `ReviewResult` per the brief.
4. **Diff fetch:** `fetch_pr_diff()` with 404/410-specific errors and a 100,000-character cap; a diff parser finds which right-side lines can take review comments.
5. **Baseline pass:** `run_baseline_review()`, one LLM call, never raises.
6. **Worker:** real flow (auth → diff → baseline → post → store), failure comment + `failed` run on diff or review failure.
7. **Storage:** second migration adding the M2 columns.
8. **Tracing** reworked to Langfuse best practices (from the Langfuse agent skill and the current docs page "What does a good trace look like?"): nested context-manager observations, the LLM call as a `generation` with model, parameters, token usage and cost; meaningful trace input/output; `session_id` = `<repo>#<pr>`; `environment` attribute.
9. P3/P4: `OPENROUTER_API_KEY`, `LLM_MODEL`, `LLM_MAX_TOKENS`, `LLM_TEMPERATURE` config; `fastapi` and `starlette` pinned.

### Why I am making this change
Milestone 2 brief. It produces the baseline row of the ablation table: a single LLM pass over the raw diff, measured end to end. Q44 (Alembic) is due as M2 pre-work.

### Alternatives I considered
1. **Finding fields:** keep `line` and only add fields, as the brief's "only add, never remove" said.
2. **LLM errors:** catch only `litellm.exceptions.APIError`, as the brief said.
3. **Diff return type:** return a bare `str` from `fetch_pr_diff`, as the brief's signature said.
4. **Out-of-diff findings:** post every finding as a line comment regardless.
5. **Confidence on the PR:** show the LLM's self-reported confidence in each comment, as the brief's template did.
6. **LLM tracing:** LiteLLM's built-in Langfuse callback.
7. **Migrations at start:** a separate one-shot `migrate` Compose service.
8. **`BaselineResult`:** without a `status` field, as the brief's model listed it.

### Reasons I rejected each alternative
1. **The brief's instruction was wrong.** Its own schema replaces `line` with `line_start`/`line_end`, and the range is required: Q23's location tolerance ("within the labeled range extended by ±3 lines") compares a finding against a *range*, and bugs often span several lines. Keeping `line` too would give two sources of truth. `subcategory` stays, with its Q39 `security-other` rule, although the brief's schema omitted it.
2. The installed LiteLLM 1.103.1 source shows `AuthenticationError`, `RateLimitError`, `Timeout`, `BadRequestError` and the rest are **not** subclasses of `litellm.exceptions.APIError`; all share `openai.APIError`. Catching only the former would let most failures escape `complete()`.
3. The worker must record `diff_chars` and `diff_truncated` (Steps 5–6); a truncated string cannot report its original size. It returns a small `PRDiff` model (text, original character count, truncated flag).
4. GitHub rejects an entire review (422) if any comment targets a line outside the diff. Chosen by the project owner: findings on diff lines become line comments, the rest are listed in the review body.
5. Chosen by the project owner: ADR-016 says LLM self-confidence is poorly calibrated. `raw_llm_confidence` is still stored in the finding and traced, but not shown on the PR until the precision filter exists.
6. The callback emits its own observations outside the job's span tree; a manual `generation` nests under `baseline.review` and carries exactly the fields the best-practices page requires.
7. The brief asked for `alembic upgrade head` in the api and worker commands. Two containers migrating at once can race, so `env.py` takes a Postgres advisory lock for the duration of the migration.
8. The brief requires returning `status="failed"` and the worker branches on it, so the field is required; values `success | partial | failed` (partial = some findings failed validation).

### Trade-offs I am accepting
- The `generation` input holds the full prompt, including up to 100,000 characters of diff: large traces, but they record exactly what the model saw, which evals need.
- Diff truncation at 100,000 characters is a stopgap (Q48).
- Alembic's sync engine uses the same `postgresql+psycopg://` URL as the async app: psycopg 3 serves both modes, so no separate sync URL is needed.
- Span names keep the brief's dotted form (`review.job`, `github.fetch_diff`, …). They satisfy the best-practice rule that matters (stable, no dynamic values) but are not verb-first; renaming later would break saved filters, so the choice is recorded.

### What could go wrong
- The OpenRouter key has a total spending limit of 0; every live LLM call returns 403 until the limit is raised. Steps 1–7 are tested with mocks; Step 8 is blocked until then.
- The LLM cites wrong line numbers: handled by the out-of-diff summary.
- A reviewed diff contains secrets and they are sent to OpenRouter and Langfuse cloud. Not masked in M2 (new open question).
- Posting fails after the LLM call succeeds: the run is recorded `failed` with the error; no retry except on rate limits.

### How this affects other components
- **Webhook Service**: tracing gains trace input/output; no behaviour change.
- **Job Queue**: runs the baseline pipeline instead of the dummy comment.
- **GitHub Integration**: shared httpx client, diff fetch, PR review posting.
- **Review Graph**: first node exists as `app/graph/baseline.py` (single pass, no LangGraph).
- **LLM Client**: built.
- **Finding Schema**: final M2 field set.
- **Storage**: Alembic-managed; M2 columns.
- **Tracing**: nested observations, generation with usage and cost.
- Context Builder, Precision Filter, Guardrails: untouched (the prompt's `<diff>` delimiters are the only injection defence in M2).

---

## M2 baseline reviewer: completion
**Date**: 2026-09-30
**File(s) affected**: as listed in the M2 pre-work entry, plus `app/storage/migrations/script.py.mako` (template modernised to pass ruff), `infra/docker-compose.yml` (`OTEL_SERVICE_NAME`), `app/github/client.py` (`raise_if_rate_limited`), and the vault notes GitHub Integration, Storage and Review Graph.

### What I am changing
Recording what M2 built and the decisions the brief asked to be explained, plus changes found during implementation and the Langfuse trace audit:
1. The root `review.job` observation is set to `ERROR` (failed run) or `WARNING` (partial) with a status message.
2. `set_trace_io()` removed: deprecated in Langfuse v4. Trace input/output now come from the root observation's own input/output, as the Langfuse docs describe.
3. `OTEL_SERVICE_NAME` (`themis-api`, `themis-worker`) set in Compose, so spans no longer report `unknown_service:python`.
4. The M1 `start_trace`/`end_trace`/`start_span`/`end_span` helpers were replaced by `observe()`, `trace_attributes()` and `update()`.
5. The model's `cost_usd` became nullable so Alembic revision 1 matches the deployed M1 table exactly, allowing the dev database to be stamped instead of rebuilt.

### Why I am making this change
The Langfuse skill requires running the instrumented path, fetching the real trace, and fixing gaps against the current best-practices page. A real run against the test repo produced a trace whose root showed `DEFAULT` for a failed review and whose service name was unknown.

The brief asked this entry to explain five decisions:
- **`confidence` vs `raw_llm_confidence`:** an LLM's self-reported confidence is poorly calibrated (ADR-016), so it never decides what is posted. It is kept as `raw_llm_confidence` so evals can measure that miscalibration; the decision-making `confidence` comes only from the precision filter (0.0 until M5). A `confidence` key in LLM output is discarded.
- **`<diff>` delimiters and "it is data":** PR content is untrusted and can carry instructions aimed at the reviewer (Guardrails, Q7). Until the guardrails component exists, explicit delimiters plus an instruction that delimited content is data are the only injection defence. The diff is inserted with `str.replace`, not `str.format`, because diffs contain braces.
- **`run_baseline_review` never raises:** the review pass cannot know the right response to a failure (retry, post an error comment, record a failed run); the worker can. Returning `status="failed"` with the reason in `parse_errors` keeps that decision in one place and makes failures data the eval harness can count.
- **Sync URL in migrations:** Alembic runs synchronously. psycopg 3 serves sync and async with the same `postgresql+psycopg://` URL, so migrations and the async app share one `DATABASE_URL`.
- **100,000-character diff cap:** at roughly 4 characters per token it is about 25,000 tokens, comfortably inside gpt-4o-mini's context with room for the prompt and a 2,048-token answer, and it bounds cost per PR. It is an open question (Q48) because truncation silently drops the end of large PRs; chunking or per-file review is the real fix.

### Alternatives I considered
- Leave the root level `DEFAULT` and rely on `status` in the output.
- Keep `set_trace_io()` despite the deprecation warning.

### Reasons I rejected each alternative
- Langfuse filters and dashboards work on level; burying failure in the output JSON makes failed reviews hard to find.
- It is slated for removal in a future major version, and the docs say trace I/O derives from the root observation.

### Trade-offs I am accepting
A replayed webhook for PR #1 posted a second error comment on the test repo (acceptable: test repo only).

### What could go wrong
**Live end-to-end is not complete.** Three external blockers, each recorded as an open question:
1. The GitHub App lacks **Contents: Read**. GitHub returns 403 "Resource not accessible by integration" for the diff media type (`X-Accepted-GitHub-Permissions: pull_requests=read; contents=read`). Verified with a real run.
2. The OpenRouter key has a **total spending limit of 0** ("Key limit exceeded"), so no LLM call can succeed.
3. The cloudflared quick tunnel has **0 ready connections**; GitHub's delivery log shows "failed to connect to host".

Everything downstream of those was verified with a real signed delivery to the local API: real installation token, real GitHub call, real error comment posted by the bot on PR #1, `failed` row in Postgres, and the full trace in Langfuse cloud.

### How this affects other components
- **Tracing**: root level reflects run outcome; service names set.
- **GitHub Integration**: required App permissions are now Pull requests (read & write), Contents (read), Metadata (read).

---

## Vault correction: GitHub App needs Contents: Read
**Date**: 2026-10-01
**File(s) affected**: `docs/vault/02 Architecture/GitHub Integration.md`, `docs/vault/07 Progress/Open Questions.md` (Q50 closed)

### What I am changing
Recording the GitHub App's required permission set: Pull requests (Read & write), **Contents (Read-only)**, Metadata (Read-only). No code change.

### Why I am making this change
Contents: Read is required for diff fetching and was missing from the original spec. A real M2 run got 403 "Resource not accessible by integration" on `GET /pulls/{n}` with the diff media type; GitHub's `X-Accepted-GitHub-Permissions` header named `pull_requests=read; contents=read`. The owner has added the permission and accepted it on the installation.

### Alternatives I considered
Fetch the diff another way (e.g. the PR files endpoint) to avoid the Contents permission.

### Reasons I rejected each alternative
The unified diff is the input the baseline prompt is built on; reconstructing it from per-file patches adds code for no benefit, and later milestones (repo context) need Contents: Read anyway.

### Trade-offs I am accepting
The App can read repository contents, a broader permission than before.

### What could go wrong
Installations created before the permission change must accept the updated permissions, or diff fetch keeps failing with 403.

### How this affects other components
- **GitHub Integration**: permission set corrected; no behaviour change.

---

## Free-tier four-provider LLM cascade (ADR-021)
**Date**: 2026-10-01
**File(s) affected**:
- Code: `app/llm.py`, `app/config.py`, `app/graph/baseline.py` (file-path normalisation), `app/schemas.py` (`LLMConfig.provider`), `app/worker/job.py` (provider in trace/config), `.env.example`, `tests/test_llm.py`, `tests/test_baseline.py`, `tests/conftest.py`
- Vault: `04 Decisions/ADR-021 Free-tier four-provider LLM cascade.md` (created); `06 Risks/Free Tier Throughput.md` (created); `05 Stack/` Groq, Gemini, Mistral (created), OpenRouter, LiteLLM (edited); `02 Architecture/LLM Client.md`; `00 Index.md`; `07 Progress/` Open Questions, Current Status, Session Log
- Docs: `docs/flow.md`

### What I am changing
`complete()` iterates `LLM_PROVIDER_CASCADE` (default groq → gemini → mistral → openrouter). For each provider it builds the LiteLLM model string `<provider>/<LLM_MODELS[provider]>` and the provider's API key, skips providers with an empty key, tries the call, and moves on if the provider fails. `LLMError` is raised only when every provider has failed, naming each provider and why. `LLMResponse` gains `provider`. `LLM_MODEL` (single string) becomes `LLM_MODELS` (provider → model mapping).

Model IDs, chosen from each provider's live model list and a live test call through LiteLLM 1.103.1 on 2026-10-01:
- groq: `openai/gpt-oss-120b`
- gemini: `gemini-3.5-flash` (`gemini-2.5-flash` returned 404, retired)
- mistral: `codestral-2508`
- openrouter: `qwen/qwen3.8-27b:free`

### Why I am making this change
The project runs on free tiers only; the single OpenRouter key had a spending limit of 0, and OpenRouter's free tier (~50 requests/day) is too tight to be a primary.

### Alternatives I considered
1. Fall through only on `RateLimitError`, `AuthenticationError`, or an empty key, as the brief listed.
2. One provider with retries.
3. Record `cost_usd` as 0.0 for every free-tier call.

### Reasons I rejected each alternative
1. During model selection a listed model returned 404 (gemini-2.5-flash), and Groq's free tier caps 8K tokens per minute, so a large prompt is rejected outright rather than rate-limited. Stopping the cascade on those errors would fail reviews another provider could serve, contradicting the Free Tier Throughput risk ("degrade gracefully when a provider disappears"). Every provider error falls through; the reason is recorded per provider.
2. Any single free tier's daily cap is too low for benchmark runs.
3. Free-tier spend is $0, but a zero everywhere makes the cost-per-PR metric meaningless. `cost_usd` keeps LiteLLM's list-price estimate (0.0 where it has no price, e.g. `:free` models), documented as notional.

### Trade-offs I am accepting
- Which model answered varies run to run, so results mix models. Every response records `provider` and `model`, and traces show both, so evals can stratify.
- A slow provider (gemini-3.5-flash took 51 s in the live test) slows the review when earlier providers fail.

### What could go wrong
- All four free tiers exhausted at once: the review fails with an `LLMError` listing all four reasons.
- Free tiers may use submitted prompts to improve provider models. Diffs are sent unmasked (Q49), which matters more now.
- Model IDs go stale; the fix is a config change.

### How this affects other components
- **LLM Client**: provider cascade, `provider` in responses and traces.
- **Review Graph** (baseline): file paths normalised against the diff (some models prefix `a/` or `b/`).
- **Tracing**: `llm.complete` becomes a span containing one `llm.generate` generation per provider attempt.
- **Eval Harness / CI Quality Gate / Benchmark**: throughput constraints (risk note).

---

## Cascade implementation notes and live-test blocker
**Date**: 2026-10-01
**File(s) affected**: `app/llm.py`, `app/graph/baseline.py`, `app/worker/job.py`, `tests/test_llm.py`, `tests/test_baseline.py`, `.env` (local only: obsolete `LLM_MODEL` line removed), `docs/flow.md`, `docs/vault/07 Progress/` Open Questions, Current Status, Session Log

### What I am changing
Recording changes found while building and testing the cascade:
1. `_cost()` passes `custom_llm_provider` explicitly. LiteLLM read `groq/openai/gpt-oss-120b` as provider `openai` (Groq's model ID contains a slash) and could not price it; the cost silently became 0.0. Caught by a unit test. Verified prices for all four chosen models.
2. `normalize_paths()` maps `a/`- or `b/`-prefixed file paths back to the diff's paths. In the live model test, two models (qwen on Groq and on OpenRouter) reported `b/a.py` for `a.py`, which would put every finding outside the diff.
3. `complete()` lost its `model` parameter: a single override does not fit a per-provider model mapping, and nothing called it.
4. The `review_runs.model` column stores `<provider>/<model>`, so each row records which provider answered without a new migration.
5. Every provider attempt is its own `llm.generate` generation under one `llm.complete` span, as Langfuse's best practices ask (one generation per model invocation). Skipped providers appear in the span output.

### Why I am making this change
1 and 2 fix real defects found in testing; 3–5 follow from the cascade design.

### Alternatives I considered
- Add a `provider` column with a third migration.
- Normalise file paths in `build_review()` only.

### Reasons I rejected each alternative
- `<provider>/<model>` in the existing column carries the same information without a schema change; a dedicated column can come with M3 if evals need to index on it.
- Findings are also stored, traced and later scored against benchmark labels; the path must be right at the source, not only when posting.

### Trade-offs I am accepting
The `model` column now mixes two pieces of information in one string.

### What could go wrong
**The live test (M2 Step 8) could not run.** The machine's clock is about 19,300 seconds (5 h 22 min) fast and not NTP-synchronised (`chronyc tracking`: "19346 seconds fast of NTP time"; RTC kept in local time). GitHub rejects the App JWT (`iat` in the future) with 401 "Bad credentials", and the clock is a likely cause of the cloudflared tunnel holding 0 ready connections. Fixing it needs root: `sudo chronyc makestep` and `sudo timedatectl set-local-rtc 0`. Recorded as Q53.

### How this affects other components
- **LLM Client**: cost is correct for all providers.
- **Review Graph** (baseline): findings carry the diff's file paths.
- **Storage**: `model` column format is `<provider>/<model>`.

---

## M2 live verification, and capturing model thinking in traces
**Date**: 2026-10-01
**File(s) affected**: `app/llm.py`, `docs/flow.md`, `docs/vault/03 Reliability/Tracing.md`, `docs/vault/07 Progress/` Open Questions, Current Status, Session Log

### What I am changing
1. Recording the M2 live test results (below).
2. `_call()` now records the model's thinking on each `llm.generate` generation. The output becomes an OpenAI-format assistant message `{role, content, reasoning_content}`, and `reasoning_tokens` goes in metadata.

Live test, 2026-10-01, `Daksha1611/themis-test-repo`, events delivered by GitHub through the cloudflared tunnel:
- Preconditions all passed: system clock synchronised (1 s skew vs GitHub); `/health` through the tunnel returned `{"status":"ok"}`; `GET /app` with a fresh JWT returned 200; the installation token exchange returned 201; the diff fetch returned PR #1's diff (Contents: Read live).
- **PR #2** (planted off-by-one, missing None check, divide-by-zero): one review with 3 line comments, one per planted bug. Provider **groq** (`openai/gpt-oss-120b`); 468 prompt / 909 completion tokens; list-price $0.000616; 6.1 s.
- **PR #3** (docstring and variable rename): "⚖️ Themis found no logic bugs or security issues in this diff." Provider **groq**; 407 / 123 tokens; $0.000135; 2.5 s.
- Langfuse: both `review.job` traces with all six child spans, `provider=groq` on the generation, the `llm.complete` span and the root `ReviewResult`; token usage and cost on the generation.
- Postgres: two `success` rows with non-zero `prompt_tokens`, `model=groq/openai/gpt-oss-120b`.

### Why I am making this change
The Langfuse skill requires auditing real traces against the current best-practices page, which says to always capture thinking on generations. `gpt-oss-120b` is a reasoning model (509 of 909 completion tokens were reasoning on one run), and the trace did not show any of it.

### Alternatives I considered
1. Read only `reasoning_content`.
2. Store the thinking in generation metadata.

### Reasons I rejected each alternative
1. For Groq, LiteLLM puts the thinking in `message.reasoning`, not `reasoning_content`; a live run with only the latter captured nothing.
2. Tried and verified against Langfuse: metadata values are truncated, so only the first 200 of ~2,300 characters were stored.

### Trade-offs I am accepting
The generation output is a message object instead of a plain string, so anything reading it must take `content`. The trace root's output (the `ReviewResult`) is unchanged.

### What could go wrong
Thinking can be long and may echo the reviewed code, so traces grow, and the unmasked-secrets concern (Q49) applies to it too.

The live run also showed findings use free-text categories ("logic bug", "bug") because the baseline prompt does not list the ADR-019 taxonomy. Recorded as Q54; must be fixed before M3 measures recall, since Q23 requires the correct category for a hit.

### How this affects other components
- **Tracing / LLM Client**: generations carry thinking and reasoning-token counts.
- Replaying PR #2 three times to verify the fix posted three duplicate reviews on the test PR (test repo only).

---

## M3 pre-work: CWE taxonomy, constrained categories, repo verification
**Date**: 2026-10-01
**File(s) affected**:
- Created: `app/taxonomy.py`; `evals/__init__.py`, `evals/benchmark/__init__.py`, `evals/benchmark/verify_repos.py`; `docs/vault/04 Decisions/ADR-022 CWE Top 25 security taxonomy.md`
- Edited: `app/schemas.py` (category validation), `app/graph/baseline.py` (prompt lists categories), `tests/test_baseline.py`, `tests/test_schemas.py` (created), `.gitignore` (`evals/.repos/`, `evals/.cache/`)
- Vault: ADR-009 (status → superseded), Finding Schema, Review Graph, Benchmark, Metrics, Benchmark Leakage, Glossary, 00 Index, Open Questions (Q37, Q37b, Q54 closed), Current Status, Session Log; `docs/flow.md`
- External: `Daksha1611/themis-test-repo` (all open PRs closed, their branches deleted)

This entry covers M3 pre-work A–C and Step 1 only. Steps 2–8 (mining, cases, cache, runner, metrics, report) get their own pre-work entry after the repo list is approved.

### What I am changing
1. **ADR-022:** CWE Top 25 (**2024 edition**) replaces OWASP Top 10 as the security taxonomy; ADR-009 superseded. The Python-reachable subset, verified against MITRE's CWE view 1430 (2024 Top 25, CWE 4.20): CWE-20, CWE-22, CWE-78, CWE-79, CWE-89, CWE-94, CWE-200, CWE-400, CWE-502, CWE-798, CWE-918, plus `security-other` (required subcategory, Q39).
2. **Q54:** `app/taxonomy.py` holds the allowed categories; `Finding` rejects any other category; the baseline system prompt lists every allowed category with a one-line description.
3. **Test repo cleanup:** close PRs #1–#3 on `Daksha1611/themis-test-repo` and delete their branches.
4. **Step 1:** `evals/benchmark/verify_repos.py` clones each candidate (treeless, history only) and reports bug-fix commit counts, package-only counts, linked issues, date range and distribution, and whether the changelog has a separable "fixed" section.

### Why I am making this change
Q37b decided by the project owner (CWE Top 25). Q54: with free-text categories, Q23's "correct category" condition makes recall meaningless. Q20 needs evidence before mining.

### Alternatives I considered
1. Pin the **2025** CWE Top 25 (it exists: MITRE CWE view 1435).
2. Use the brief's candidate CWE list as given.
3. Free-text category with fuzzy matching at scoring time.
4. Count only commits touching *exclusively* package `.py` files.

### Reasons I rejected each alternative
1. The 2025 list drops CWE-798 (hard-coded credentials) and CWE-400 (uncontrolled resource consumption), two of the weaknesses most visible in a Python diff. Its additions are memory-buffer (120/121/122) and access-control (284, 639, 770) entries, mostly unreachable in Python or overlapping 400. The 2024 list fits Python code review better, and it is the edition the brief named.
2. CWE-327 (broken crypto) and CWE-611 (XXE) are in neither the 2024 nor the 2025 Top 25; they fall under `security-other`. CWE-94 (code injection: `eval`/`exec`), CWE-79 (XSS from Python HTML/template code) and CWE-200 (information exposure) are Top 25 entries reachable in Python and are added. CWE-77 is left to its Python-relevant child CWE-78. Memory-safety entries (787, 125, 416, 119, 190, 476) are excluded (Python is memory-safe; 476 overlaps `null-or-none-handling`), as are authentication/authorisation entries (287, 306, 862, 863, 269, 352, 434), which are application-level and rarely visible in one diff.
3. Fuzzy matching hides model errors instead of measuring them; an invalid category is a parse error.
4. Good fixes usually ship with a test, so "only package files" would discard most of the best cases. The script reports both: commits whose *non-test, non-doc* changes are all package `.py` (used for viability), and commits touching package `.py` files exclusively.

### Trade-offs I am accepting
- Eleven CWE categories plus seven logic categories make a long prompt (~40 lines of category list) and a harder classification task; category confusion will show up as the gap between location-only and category-correct recall.
- Pinning 2024 means the taxonomy is one edition behind from the start (recorded in ADR-022).

### What could go wrong
- The model picks a plausible but wrong category (e.g. CWE-20 versus a specific CWE), lowering category-correct recall; tracked by per-category metrics.
- Treeless clones still download all commit and tree objects in the window; large repos make Step 1 slower.

### How this affects other components
- **Finding Schema**: `category` restricted to the taxonomy.
- **Review Graph** (baseline): prompt lists the categories.
- **Benchmark / Metrics**: security labels use CWE IDs.

---

## M3 Step 1 results and small additions
**Date**: 2026-10-01
**File(s) affected**: `pyproject.toml` (ruff per-file ignore for `evals/*`: S603, S607), `evals/benchmark/data/repo_verification.json` (created), `docs/vault/03 Reliability/Benchmark.md`, `docs/vault/06 Risks/Benchmark Leakage.md`, `docs/flow.md`

### What I am changing
1. Recording the repo verification results (table in `Benchmark.md`, date distribution in `Benchmark Leakage.md`).
2. Allowing ruff's subprocess rules in `evals/`: the eval scripts invoke `git` with fixed arguments by design.
3. Raising Q55 (no arithmetic-error category) and Q56 (size-filter scope).

### Why I am making this change
The brief requires the table before mining. Q55 came from the live category check; Q56 from estimating Step 2's yield.

### Alternatives I considered
Suppress S603/S607 inline at each call site.

### Reasons I rejected each alternative
Every subprocess call in the eval tooling is a `git` call with fixed arguments; one documented per-directory rule is clearer than repeated inline suppressions.

### Trade-offs I am accepting
A future subprocess call in `evals/` taking untrusted input would not be flagged.

### What could go wrong
With only three viable repos the case count may land near the bottom of the 150–300 target after Step 2's filters and Step 3's discards.

### How this affects other components
None; tooling and documentation only.

---

## Vault consistency audit and hardening: pre-work
**Date**: 2026-10-01
**File(s) affected** (planned; Part B's exact list depends on the approved audit report):
- Part A: none (read-only audit, report shown before any fix)
- Part B: vault notes named in the approved report
- Part C: `docs/vault/00 Brief.md` (create); the local project rules file (reading order). It is git-excluded, so it never reaches the repo.
- Part D: `scripts/check_vault.py` (create), `tests/test_check_vault.py` (create), `.github/workflows/ci.yml` (`vault-check` job)
- Part E: the local project rules file ("Verify before trusting" section)
- Part F: `docs/vault/09 External Facts.md` (create)
- `docs/vault/07 Progress/` Current Status, Session Log


### What I am changing
A maintenance pass, no application code and no M3 work. Audit the whole vault against the code, `docs/flow.md`, installed packages and itself (Part A); after approval, fix notes to match reality (B); add a short mandatory-first-read brief (C); add a mechanical checker run in CI so drift fails the build (D); add verification rules to the local project rules file (E); add a register of external facts that expire (F).

### Why I am making this change
M3 depends on the vault being accurate. Several decisions were superseded or extended in M1–M3 pre-work (ADR-009, ADR-010, ADR-005 by ADR-021), and nothing checks the vault mechanically.

### Alternatives I considered
1. Fix inconsistencies while auditing.
2. Run the checker as a pre-commit hook only.

### Reasons I rejected each alternative
1. The owner asked to see the report before any fix; some findings need a decision, not a correction.
2. A pre-commit hook can be skipped locally; a CI job fails the build for everyone, like a lint error.

### Trade-offs I am accepting
The checker makes vault conventions strict: every note change must keep frontmatter, links and numbering valid, or CI fails.

### What could go wrong
- The checker's rules must match the vault's real conventions, or it fails on valid notes. Where the requested rules conflict with existing conventions, the audit report flags it for a decision.
- The local project rules file is not in git, so CI cannot check it.

### How this affects other components
None at runtime. CI gains a `vault-check` job.

---

## Vault consistency audit and hardening: completion
**Date**: 2026-10-02
**File(s) affected**:
- Created: `docs/vault/00 Brief.md`, `docs/vault/09 External Facts.md`, `docs/vault/05 Stack/starlette.md`, `docs/vault/05 Stack/pytest-asyncio.md`, `scripts/check_vault.py`, `tests/test_check_vault.py`
- Edited: every vault note (frontmatter); bodies of Architecture Overview, Webhook Service, Job Queue, GitHub Integration, Finding Schema, Storage, LLM Client, Review Graph, Benchmark, CI Quality Gate, Drift Monitoring, Eval Harness, Metrics, Tracing, Glossary, Prior Art, 00 Index, Open Questions, ADR-004, ADR-005, the risk notes Benchmark Leakage, Eval Cost, Free Tier Throughput, Hosting and Scope Creep, the stack notes Docker, GitHub Actions, pytest, pytest-cov, LiteLLM, OpenRouter, PostgreSQL, Pydantic, httpx, Qdrant and FastAPI; `Themis Map.canvas`; `docs/flow.md`; `README.md`; `app/main.py` (one duplicated comment line removed); `.github/workflows/ci.yml` (`vault-check` job); the local project rules file (not in git)

### What I am changing
Applied the owner's approval of the Part A report, then Parts C–F. **The approval (2026-10-02):** the nine recommendations with three amendments: #2 (an empty `version:` is allowed only while `planned`, no "not installed" marker), #5 (eval output has two destinations: case-level `results.jsonl`, run-level summaries in the eval database for the M7 gate; resolved, not an open question), #7 (public repositories only, stated in the README; Q49 retitled to the masking work). Plus two extra fixes (F1 Eval Cost as a request budget; F2 three repos and raw counts) and an M3 reporting requirement.

**How the work was done:** a second local session, told only "continue", applied the nine recommendations *without* the amendments, and had also inserted an approval paragraph into the pre-work entry above, describing an approval that was never given in that form. That paragraph was removed and the pre-work entry restored as written; this session then applied the amendments on top (items 18–24). Every correction makes a note match the code or the live system; nothing in the code was changed to match a note.

**Frontmatter and conventions**
1. `name` (= filename) and a one-line `description` added to all 91 notes, so check 5 can run.
2. `status` now has a defined meaning per type, written in the Glossary: tech `planned` = not installed, `in-progress` = installed but not yet used by code, `done` = installed and in use; risk `planned` = no mitigation, `in-progress` = partly mitigated, `done` = mitigated. The middle tech value was not in the approved recommendation; it covers Qdrant (runs in Compose, no code uses it) and pytest-cov (installed, not run in CI).
3. Statuses corrected: Webhook Service and LLM Client `done`; Architecture Overview, Benchmark and CI Quality Gate `in-progress`; 26 installed stack notes `done`, Qdrant and pytest-cov `in-progress`; risks Benchmark Leakage, Eval Cost, Free Tier Throughput and Scope Creep `in-progress`, Hosting and Label Noise stay `planned`.
4. Stack versions: the seven uninstalled `planned` notes have an empty `version:` (amendment #2; first written as `not installed`, then emptied). GitHub Actions now records its action pins and runner. Docker.md frontmatter repaired: a `related:` entry had been appended under `version:`, which made the frontmatter invalid YAML.
5. Open Questions: every entry is now `- **Q<n>.** …`. The old numbered-list form also rendered wrongly, because Markdown renumbers ordered lists (the Milestones section showed 50–56 instead of 50–53, 44–46). Q20 and Q25 no longer appear twice: their partial resolutions moved into the open entries. Q37 is no longer listed three times: Q37 (OWASP edition) and Q37b (CWE replaces OWASP) are separate entries. Q20, Q55 and Q56 are marked as blocking M3. Q49 records the decision on public diffs. New Q57 records where eval results go.

**Superseded decisions (A1)**
6. ADR-005 keeps `accepted`, with a banner saying ADR-021 amended it (LiteLLM stays; OpenRouter-only routing is replaced).
7. Architecture Overview diagram: the LLM Client points at the four-provider cascade instead of OpenRouter alone; eval results go to `results.jsonl` and the cache, and the eval database only holds the CI gate's history.
8. LLM Client, LiteLLM, OpenRouter, Drift Monitoring, Prior Art and Eval Cost no longer describe OpenRouter-only routing, a "cheap model" or OWASP as current.

**Notes against code (A2, A3)**
9. `docs/flow.md`: rows added for `build_messages`, `parse_findings`, `format_finding`, `github_headers`, `get_langfuse`, `init_tracing`, `shutdown_tracing`, `redis_settings`, `_ignored`, `_exit`, `_Run.row`, `run_migrations_online` and `run_migrations_offline`. The two non-function rows became `Finding._check()` and `run_migrations_online()`. Section 2 now describes the root `ERROR`/`WARNING` level, and sections 1, 2 and 8 describe `OTEL_SERVICE_NAME`.
10. Component notes: each marks what is built (M2) and what is planned. Finding Schema marks `ReviewContext` as not in code and adds `LLMConfig.provider`. Storage lists the real `review_runs` columns and says `model` holds `<provider>/<model>`. Job Queue describes the real M2 flow and the retry rules. Webhook Service lists every response, including the 400 and 200-ignored ones. "Planned code location" became "Code location" wherever the code exists.

**Contradictions (A8)**
11. Eval results (amendment #5, resolved, not an open question): **two destinations.** Case-level results (one record per benchmark case; large; regenerable) go to `results.jsonl` files, the M3 artifact, backed by the SQLite response cache. Run-level summary metrics (one row per eval run: precision, recall, cost, latency, git SHA, split, timestamp; small; must persist) go to the dedicated eval database, consumed by the CI quality gate in M7. Stated in Eval Harness, Storage, CI Quality Gate, PostgreSQL and the Architecture Overview. An open question (Q57) first created for this was withdrawn.
12. Metrics: precision, false-positive rate, cost per PR, latency and parse error rate now have definitions, taken from the M3 brief. Recall and exact-line accuracy are defined over the finding's line range. Glossary entries for Finding, bug recall and comment precision match.
13. Benchmark and Benchmark Leakage: the "~5 repos" and "after the primary model's training cutoff" wording now matches the verified window and the three viable repos.
14. **Found while fixing, not in the report:** ADR-004 said hybrid search was "BM25 + embeddings", while ADR-015 (Q13) settled on Qdrant native sparse vectors with no separate BM25 index. ADR-004 gets a "refined by ADR-015" banner. ADR-015 is clearly the later and more specific decision, so this needed no open question.

**Outside the vault**
15. README status line was "planning, no application code"; it now states M1–M2 built and M3 in progress, and says the training-set guard is planned. (The `app/main.py` comment change and the CI job are logged in separate entries below.)

**Parts C–F**
16. `00 Brief.md` (52 lines) is the mandatory first read. `09 External Facts.md` is seeded from checks run on 2026-10-02:
   - each provider's model listed live and test-called;
   - Groq and Mistral limits read from response headers;
   - the App's permissions read from `GET /app/installations`, plus a real diff fetch;
   - library versions read from the installed packages;
   - MITRE checked for a newer CWE edition.
   The local rules file gains the Brief as step 1, "Verify before trusting", the 30-day re-verification rule, and running the checker before committing.
17. `scripts/check_vault.py` implements the seven checks with the standard library only, so the CI job installs nothing. Beyond the brief:
   - check 1 also runs in reverse (every function in `app/` must have a row; recommendation 8);
   - check 4 rejects numbered-list entries, so the old form cannot hide a duplicate;
   - check 7 also requires a pinned package's note to state the pinned version.
   `tests/test_check_vault.py` builds a valid fixture repo and breaks it 17 ways. Each check fails on its own breakage, and only that check fails.

**Amendments applied on top (this session)**
18. **Check 7** (amendment #2): no "not installed" marker. An empty `version:` passes only when `status: planned`; empty with any other status fails. Tests: empty-but-not-planned fails; planned-and-empty passes.
19. **Check 1 exemptions as rules** (as approved): everything under `app/storage/migrations/` (revision `upgrade`/`downgrade` and `env.py` internals), dunder methods, Pydantic validators, and **private leaf helpers**: a `_name` function that calls no function defined in `app/` (covers `_exit`, `_Run.row`, `_ignored`, `_cost`). Rows for exempt functions may still exist and are still checked for existence. Tests: env.py and a private leaf need no row; a private helper that calls app code does. The two non-function rows needed no marker: they were rewritten as real function rows (`Finding._check()`, `run_migrations_online()`), which removes the need for any tolerance.
20. **Public repositories only** (amendment #7): README gains a Limitations section; the Brief lists it as a hard constraint; Q49 retitled "Secret masking for private-repo support", recording that some providers' free-tier terms permit using submitted data (Google's Gemini API free tier states this). Private-repo support is out of scope for v1.
21. **F1:** Eval Cost rewritten in terms of request budget (requests and tokens per day/minute per provider, not dollars), cross-linked with Free Tier Throughput; both notes now carry the same joint mitigation list (response cache, dev-split-only CI runs, batched first run, cascade).
22. **F2:** Benchmark says three repos (click, anyio, fastapi; final confirmation Q20) and requires per-category recall with raw counts, never bare percentages (also in Metrics). Benchmark Leakage records that the 2025-04-01 window start is what reduced the viable set.
23. **M3 reporting requirement** (Benchmark Leakage): M3 Step 1 must output the date distribution of the actually-mined commits by quarter; if a substantial fraction predates mid-2025, the caveat goes on the public results page itself.
24. **External Facts:** all 19 pinned packages with installed versions (read via `importlib.metadata`, all match); Groq's 8,000 tokens/minute marked as the binding constraint.
25. **Owner approval (2026-10-02)** of the second session's three departures: tech `in-progress` means installed but not yet used by code; the two non-function call-graph rows became real function rows; ADR-004 carries a "refined by ADR-015" banner. All three kept.

### Why I am making this change
M3 is about to depend on the vault. The audit found drift that a reader could act on wrongly: for example the eval-results location, `ReviewContext` described as built, OpenRouter presented as the only provider, and metric definitions missing. A checker in CI turns the mechanical part of that drift into a build failure.

### Alternatives I considered
1. Leave `status` meanings undefined, and only fix the clearly wrong values.
2. Put the checker in pytest instead of a separate CI job.
3. Parse frontmatter with PyYAML, which is installed as a transitive dependency.

### Reasons I rejected each alternative
1. Without defined meanings, 25 stack notes said `in-progress` while fully in use, and no check could be written.
2. A separate job shows vault drift as its own failure, and it needs no install step.
3. Relying on a transitive dependency would break silently if it were dropped; the vault uses a small YAML subset that the standard library parses in about 40 lines.

### Trade-offs I am accepting
- Every note edit must keep frontmatter, links and numbering valid, or CI fails.
- Every new function in `app/` needs a call-graph row in the same change.
- `description` lines can themselves go stale; no check can catch that.

### What could go wrong
- The checker validates structure, not meaning. A wrong statement in valid form still passes, which is why the Brief and the 30-day rule exist.
- **OpenRouter's model `qwen/qwen3.8-27b:free` returned 429 ("temporarily rate-limited upstream") on both test calls on 2026-10-02.** It is still listed, and it answered on 2026-10-01. It is the last fallback, so reviews still succeed through Groq, Gemini or Mistral. Recorded in External Facts; to be re-checked before M3's long runs.
- The local rules file is not in git, so CI cannot check it.

### How this affects other components
No runtime behaviour changes. Future sessions read `00 Brief.md` first. Code-adjacent changes are logged separately below.

---

## Remove a duplicated comment in app/main.py
**Date**: 2026-10-02
**File(s) affected**: `app/main.py`

### What I am changing
Deleting one of two consecutive comment lines in `lifespan()` that said the same thing ("Schema is managed by Alembic … `alembic upgrade head` runs before the app starts"). **Comment-only; no behavioural effect.**

### Why I am making this change
Found by the vault audit (Part A); approved by the project owner.

### Alternatives I considered
Leave it until the next code change in `app/main.py`.

### Reasons I rejected each alternative
The owner approved the fix now; deferring leaves a known defect for no benefit.

### Trade-offs I am accepting
None.

### What could go wrong
Nothing at runtime; tests, ruff and mypy confirm the file is otherwise unchanged in behaviour.

### How this affects other components
None.

---

## Add the vault-check CI job
**Date**: 2026-10-02
**File(s) affected**: `.github/workflows/ci.yml`

### What I am changing
A second job, `vault-check`, runs `python scripts/check_vault.py` on every push and pull request, alongside the existing `test` job. It installs nothing (the checker uses the standard library only).

### Why I am making this change
Part D of the vault audit: vault drift should fail the build the same way a lint error does.

### Alternatives I considered
1. Run the checker inside the `test` job.
2. A pre-commit hook.

### Reasons I rejected each alternative
1. A separate job reports vault drift as its own failure and needs no dependency install.
2. Hooks can be skipped locally; CI cannot.

### Trade-offs I am accepting
Any vault edit that breaks links, numbering or frontmatter now fails CI.

### What could go wrong
The checker's rules could reject a valid new convention; the fix is to change the checker and its tests in the same change.

### How this affects other components
CI only.

---

## M3: decisions on Q20, Q55, Q56; Steps 2–3 (mine commits, build cases): pre-work
**Date**: 2026-10-02
**File(s) affected**:
- Code: `app/taxonomy.py` (new category, shared precedence rules), `tests/test_schemas.py`, `tests/test_baseline.py`, `evals/benchmark/verify_repos.py` (shared repo list and constants), `evals/benchmark/mine_commits.py` (create), `evals/benchmark/build_cases.py` (create), `evals/benchmark/labeling.py` (create), `tests/test_benchmark.py` (create)
- Data (created): `evals/benchmark/data/candidates.jsonl`, `evals/benchmark/data/dev.jsonl`, `evals/benchmark/data/holdout.jsonl`, `evals/benchmark/data/build_report.json`, `evals/benchmark/data/sample_for_review.md`
- Vault: `04 Decisions/ADR-023 Arithmetic-or-numeric logic category.md` (create); ADR-019 (banner); Glossary, Finding Schema, Benchmark, Metrics, Benchmark Leakage, Open Questions (Q20, Q55, Q56 closed; Q58, Q59 added), 00 Index, 00 Brief, Current Status, Session Log
- `docs/flow.md` only if `app/` gains functions (call graph)

### What I am changing
**Owner decisions:**
1. **Q20:** five repos: `pallets/click`, `agronholm/anyio`, `fastapi/fastapi`, `marshmallow-code/marshmallow`, `Textualize/rich`. Drop `encode/httpx` and `encode/httpcore`.
2. **Q55:** add `arithmetic-or-numeric` (ADR-023, amending ADR-019), with precedence rules shared verbatim by the taxonomy module (and so the prompt), the Glossary, and the Step 3 labelling rules.
3. **Q56:** the size filter counts package source only; the buggy PR reverts package source only (never tests, changelogs or docs).

**Step 2, `mine_commits.py`:** for each repo, walk non-merge commits in the fixed window 2025-04-01 → 2026-10-01 and apply these filters in order:
- bug-fix message;
- package-scoped (at least one package `.py` file; every other file is a test, doc or CI file);
- ≤3 package source files and ≤60 changed package source lines;
- the subject line does not suggest a refactor, typo, docs, formatting, dependency or version bump, release or revert.

It emits `candidates.jsonl` and counts survivors per filter per repo.

**Step 3, `build_cases.py`:**
- **Buggy case:** `git diff <fix> <parent> -- <package source files>`, i.e. the fix reversed and presented as the proposed change. Its labels are the line spans the fix touched, expressed in the buggy (new) side's line numbers.
- **Cosmetic discard:** dropped when the package source ASTs before and after the fix are identical after removing docstrings (whitespace and comments) or differ only by a consistent one-to-one identifier renaming.
- **Category:** inferred by keyword and code-shape rules that apply the taxonomy's precedence rules; null when no single category clearly wins.
- **Clean case:** a non-bug-fix commit in the same repos, dated at least 6 months before the window end. Its package source files received no package-scoped bug-fix commit in the following 6 months, and it isn't cosmetic. Clean cases are sampled to match the buggy size distribution, at ~30% of the total; the diff is the commit's package source only.
- **Splits:** 60/40, stratified by repo × category (clean and null as their own strata). Case ID = first 16 hex characters of SHA-256 of `repo:sha`.
- **Review sample:** 15 cases drawn from the **dev** split only.

### Why I am making this change
Owner decisions on the three questions blocking M3, and the M3 brief Steps 2–3. The ≥40-commit bar was a per-repo heuristic; what matters is total case count and category diversity, and on three repos anyio's concurrency-heavy set would dominate overall recall.

### Alternatives I considered
1. Label categories with an LLM.
2. Take the review sample from all cases.
3. Show tests in clean-case diffs but not in buggy ones.
4. Use the window end relative to "today".

### Reasons I rejected each alternative
1. It spends free-tier quota and makes labels depend on the same kind of model being measured (circular); keyword and shape rules are reproducible and their uncertainty is visible as null labels.
2. Hand-checking holdout cases would expose holdout content; label noise estimated on dev applies to the whole set.
3. Diff shape would then reveal the class (tests present means clean). Both kinds show package source only.
4. Mining must be reproducible; the window is fixed at 2025-04-01 → 2026-10-01 and each repo's HEAD SHA is recorded.

### Trade-offs I am accepting
- Keyword-based categories will leave many cases unlabeled; those still count for location-only recall.
- "No bug fix in the following 6 months" is a heuristic, not proof that a clean case is bug-free.
- Small strata (one case) all go to dev, so rare categories may be missing from the holdout.

### What could go wrong
- Label spans for deletion-only reverts (the fix added lines, so the revert only removes them) have no new-side line; such spans use the line at the deletion point.
- Fix commits that mix a bug fix with unrelated edits produce wide labels; the ≤60-line filter limits this, and the 15-case review measures it.
- Clones advance as repos receive commits; commits inside the fixed window are stable.

### How this affects other components
- **Finding Schema / Review Graph:** one more logic category, so the prompt lists 8 logic categories.
- **Benchmark / Metrics:** case data, micro and macro recall, raw counts.
- No runtime path changes besides the taxonomy.

---

## M3 Steps 2–3: results and departures
**Date**: 2026-10-02
**File(s) affected**: as in the Steps 2–3 pre-work entry, plus `tests/test_benchmark.py`; `evals/benchmark/data/mining_report.json`; vault: Benchmark, Benchmark Leakage, Open Questions (Q60, Q61), Current Status, Session Log

### What I am changing
Recording what Steps 2–3 produced:
- **Mining:** 180 candidates. Survivors after each filter, per repo: click 446→109→65→55→47; anyio 318→96→67→60→56; fastapi 2046→128→58→53→41; marshmallow 144→31→26→23→17; rich 196→31→24→24→19.
- **Buggy cases:** 168, after discarding 12 non-behavioural fixes (6 annotation-only, 5 whitespace/comment/docstring, 1 consistent rename).
- **Clean cases:** 25. **Total 193:** dev 117, holdout 76.
- **Category labels:** 102 of 168 buggy cases have none.

**Departures from the pre-work plan:**
1. The cosmetic discard also covers **annotation-only** changes. Type hints do not change runtime behaviour, so such a fix is not a bug the reviewer could detect.
2. Clean candidates use the same "package-scoped", size and subject filters as buggy candidates, so the two classes look alike.

### Why I am making this change
M3 brief Steps 2–3; the owner asked to stop here before any free-tier quota is spent.

### Alternatives I considered
1. Relax my own clean-candidate filters (subject wording, side files) to reach the clean target.
2. Change the Q22 6-month rule to a function-level rule myself.

### Reasons I rejected each alternative
1. It adds only about 11 cases outside rich (66 in total, 37 of them from rich), skewing the clean set towards one repo.
2. Q22 is an owner decision; the shortfall is recorded as Q60 with options.

### Trade-offs I am accepting
Until Q60 is decided, clean cases are 13% of the set instead of ~30%, and smaller than the buggy cases.

### What could go wrong
A spot check found label noise the hand-check must measure:
- a feature commit ("Add follow_symlinks argument …") that matched the bug-fix pattern through its body;
- a typing-only fix ("fix typing") that is a behavioural AST change but not a runtime bug;
- wide labels (113 of 168 buggy cases have several spans, up to 23).

### How this affects other components
- **Benchmark:** first real case set.
- **Metrics:** category-correct recall rests on 66 labeled cases until Q61 is decided.

---

## M3: decisions on Q60, Q61, wide labels, macro floor, ADR-023 clause: pre-work
**Date**: 2026-10-03
**File(s) affected**:
- Code: `app/taxonomy.py` (new precedence rule), `evals/benchmark/mine_commits.py` (strip trailers), `evals/benchmark/build_cases.py` (SZZ clean rule, frozen splits, no sample file), `evals/benchmark/szz.py` (create), `evals/benchmark/label.py` (create), `tests/test_benchmark.py`, `tests/test_label.py` (create), `tests/test_schemas.py`
- Data: `evals/benchmark/data/candidates.jsonl`, `dev.jsonl`, `holdout.jsonl`, `build_report.json`, `mining_report.json` (regenerated); `sample_for_review.md` (deleted: the labelling pass replaces it)
- Vault: ADR-023, Glossary, Benchmark, Metrics, Open Questions (Q60, Q61 closed), 00 Brief, Current Status, Session Log

### What I am changing
1. **Q60, SZZ-style clean rule:** a commit is clean if none of the lines it added or modified were changed by a later bug-fix commit within 6 months. For every later bug-fix commit, `git blame` its removed lines at its parent (as the SZZ algorithm does) to find the commits that introduced them; a clean candidate is excluded if it is among them. Clean candidates pass the same filters as buggy ones (package source only, ≤3 files / ≤60 lines, behavioural change). They are sampled per size bucket to match the buggy distribution, ~30% clean overall; any bucket shortfall is accepted and reported.
2. **Frozen splits:** every case already in `dev.jsonl` / `holdout.jsonl` keeps its split. New cases join each repo × category stratum in case-ID order, filling towards 60/40 without moving existing members.
3. **Q61, `label.py`:** a resumable terminal tool for human labels on dev cases. It refuses holdout without `--freeze`, writes `labels_human.jsonl` after every case, can go back one case, and makes no LLM calls.
4. **ADR-023 clause:** index and length arithmetic (`len(x) - 1`, range bounds, slice ends) → `off-by-one-or-boundary`; `arithmetic-or-numeric` covers computed values, not positions. It goes into `PRECEDENCE_RULES`, so the prompt, the Glossary and the labelling tool's help all show it.
5. **Metrics (recorded now, built in Step 6):** strict recall (the human-marked primary range) beside lenient recall (any range); a chance baseline with no LLM calls; false-positive rate per size bucket; macro recall only over categories with ≥5 labeled cases.
6. **Commit-trailer stripping:** mined commit messages drop `Co-authored-by:` and `Assisted-by:` trailer lines. Upstream messages carried AI-assistant trailers into tracked data files; the trailers carry no case information.

### Why I am making this change
Owner decisions on Q60 and Q61 and on the follow-ups from the Steps 2–3 report. Item 6 comes from the no-mention rule: the previous commit's data files contained such trailers verbatim.

### Alternatives I considered
1. Re-run `assign_splits` on the full case set.
2. Single-keypress input (raw terminal mode) for the labelling tool.
3. Blame every candidate's lines forward instead of blaming the fixes.

### Reasons I rejected each alternative
1. Adding clean cases would shift positions inside strata and move existing cases between dev and holdout; splits are frozen.
2. Line input (`y`, then Enter) works in every terminal, is easy to test with scripted input, and needs no extra code paths for terminal restore.
3. Blaming each fix once (~100 fixes per repo) is the standard SZZ direction and is much cheaper than tracking every candidate line forward.

### Trade-offs I am accepting
- SZZ inherits its known limits: fixes that only add lines blame nothing, and blame stops at the shallow-clone boundary (2025-03-01), which is before every candidate.
- Line-based input costs one Enter per answer.

### What could go wrong
- The SZZ rule may still leave some size buckets short; reported as a shortfall.
- `git blame` over many ranges is slow on fastapi's history; acceptable for a one-off build.

### How this affects other components
- **Review Graph:** the prompt gains the ADR-023 clause.
- **Benchmark / Metrics:** new clean set; human labels; new metric definitions.

---

## M3: Q60, Q61 and follow-ups: completion
**Date**: 2026-10-03
**File(s) affected**: as in the pre-work entry above, plus `docs/vault/06 Risks/Label Noise.md`; `evals/benchmark/data/sample_for_review.md` deleted

### What I am changing
Results:
- **SZZ clean rule:** 70 clean cases (target 72), so 238 cases in total (168 buggy, 70 clean, 29% clean), dev 143 / holdout 95.
- **Size match:** clean per bucket is 26 / 22 / 14 / 8 against targets 26 / 22 / 14 / 10, so only the 31–60-line bucket is short. Median changed lines: buggy 11, clean 10 (it was 4 under the per-file rule).
- **Frozen splits held:** the build refuses to run if any existing case would change split, or if the buggy set changed, and neither happened.
- **Labelling tool:** built and tested; the holdout split is refused without `--freeze`.
- **Commit trailers:** stripped from mined messages; the data files now contain no AI-assistant trailers.

Details found while building:
1. Two click bug-fix commits sit at the shallow-clone boundary (no parent in the clone), so SZZ cannot blame them. They are skipped and counted in the funnel.
2. My first trailer-stripping edit silently did not apply (a text replacement that matched nothing), and the re-mined data still contained the trailers. The stripping is now a named, tested function, `clean_message()`, also applied to frozen cases loaded from the old files.
3. In the previous commit (`2415208`), the no-mention check printed its match count but did not gate the commit, so data files with upstream AI-assistant co-author trailers were pushed. From now on the commit runs only if the staged additions contain no such mention.

### Why I am making this change
Owner decisions on Q60 and Q61 and the follow-ups.

### Alternatives I considered
Rewrite the pushed commit `2415208` to remove the trailers from history.

### Reasons I rejected each alternative
It needs a force-push to a public repository's main branch; that is the owner's decision, not taken here.

### Trade-offs I am accepting
The trailers remain in the history of commit `2415208` until the owner decides.

### What could go wrong
- SZZ attribution can miss bugs (fixes that only add lines; lines changed again before the fix).
- The labelling pass depends on a single annotator.

### How this affects other components
- **Benchmark:** final M3 case set pending labels.
- **Metrics:** definitions for Step 6.
- **Review Graph:** the prompt carries the new ADR-023 clause.

---

## No history rewrite for mined commit trailers
**Date**: 2026-10-03
**File(s) affected**: `docs/decision.md`, `docs/vault/03 Reliability/Metrics.md`

### What I am changing
Recording the owner's decision not to rewrite history or force-push. Commits `2415208` and `4951eb5` keep the upstream commit trailers they contain. Also recording one Step 6 metric rule: the false-positive rate is reported per repo as well as per size bucket.

### Why I am making this change
The trailers are upstream maintainers' own commit attributions inside mined third-party data, not a statement about this project. The forward fix is sufficient: trailers are stripped when mining (`clean_message()`), and commits are gated on staged additions. The stripping is cosmetic: it does not affect case IDs, labels, diffs or any other case content. The per-repo false-positive rate is needed because `Textualize/rich` supplies 17 clean cases against 16 buggy, a much larger clean share than other repos, so a per-repo difference in reviewer behaviour could move the overall rate unnoticed.

### Alternatives I considered
Rewrite the two commits and force-push to `main`.

### Reasons I rejected each alternative
Owner decision: a force-push rewrites public history for content that is third-party data, not a statement about this project.

### Trade-offs I am accepting
The two commits' history keeps the upstream trailers.

### What could go wrong
Nothing at runtime.

### How this affects other components
- **Metrics:** false-positive rate per repo (Step 6).

---

## M3 Step 3b: dev-split labelling, grounded in upstream evidence: pre-work
**Date**: 2026-10-03
**File(s) affected**:
- Created: `evals/benchmark/fetch_evidence.py` (read-only GitHub fetch), `evals/benchmark/write_labels.py` (writes label records in the labelling tool's schema), `evals/benchmark/label_report.py`, `evals/benchmark/data/labels_human.jsonl`, `docs/vault/08 Results/label-report-dev-2026-10-03.md`
- Edited: `.gitignore` (`evals/.cache/` already ignored; evidence is cached there), `docs/vault/03 Reliability/Benchmark.md`, `docs/vault/07 Progress/Open Questions.md` (Q61 amendment), Current Status, Session Log, 00 Brief

### What I am changing
**Q61 amended (owner, 2026-10-03):** the owner cannot hand-label the dev split. The development assistant (an LLM, and not one of the four reviewer models) labels it instead, under two conditions: every judgement must follow reading the upstream evidence for the case, and the owner's labelling rules (drop reasons, category precedence, primary range) apply as written.

**Evidence per dev case**, fetched read-only from GitHub and cached under `evals/.cache/evidence/` (git-ignored):
- the pull request the commit came from (`GET /repos/{repo}/commits/{sha}/pulls`), with its description, conversation, review comments and reviews, including bot comments;
- every issue it links to ("Fixes #N"), with its description and comments.

**Records** are written to `labels_human.jsonl` in the labelling tool's schema, plus `labeller` ("assistant, evidence-grounded") and `evidence` (the URLs read). No GitHub writes of any kind: no comments, reviews, reactions or commits upstream. No LLM API calls, and the holdout split is not touched.

### Why I am making this change
The owner asked for it, and asked that labels follow a real understanding of each case, using the upstream PRs and their comments.

### Alternatives I considered
1. Label from the diff and commit message alone.
2. Use one of the cascade reviewer models to label.

### Reasons I rejected each alternative
1. Many fixes need the issue report to know what behaviour was wrong; without it, labels are guesses.
2. The reviewer models are the ones being measured; labels from them would make category-correct recall measure self-agreement.

### Trade-offs I am accepting
- **Limitation, stated in Benchmark.md:** the labels are LLM-made, grounded in human-written upstream evidence, not independent human labels.
- Category-correct recall therefore measures agreement between the reviewer and an evidence-grounded labeller from a different model family.
- There is still a single annotator.

### What could go wrong
- Upstream discussions can be ambiguous; such cases are dropped `o` with a note rather than guessed.
- A commit pushed directly, with no PR, has only its issue (if any) as evidence; this is noted per case.

### How this affects other components
- **Benchmark:** human-labels section amended.
- **Metrics:** category-correct recall rests on these labels.

---

## M3 Step 3b: dev-split labels, label report: completion
**Date**: 2026-10-03
**File(s) affected**:
- As in the pre-work entry above.
- Also edited: `docs/vault/03 Reliability/Metrics.md`, `docs/vault/06 Risks/Label Noise.md`, `docs/vault/08 Results/README.md`, `docs/vault/00 Index.md`.
- Created: `tests/test_label_report.py`.

### What I am changing
**Results** (full report: `docs/vault/08 Results/label-report-dev-2026-10-03.md`):
- All 143 dev cases labelled. Buggy: 80 of 102 kept, 22 dropped (2 feature, 8 typing-only, 1 refactor, 2 not-a-bug, 9 other, 8 of which are `external-compat`). Clean: 3 of 41 suspicious.
- Label noise: 21.6% upper bound (every drop reason); 12.7% excluding `o`.
- Macro-eligible categories (≥5 kept): type-or-contract 34, control-flow 17, concurrency-or-async 9, error-handling 7.
- Security: 2 kept cases, CWE-20 and CWE-400. The CWE-400 case is GHSA-5p39-cfhj-2xmp / CVE-2026-64847.
- Heuristic category on kept cases: agreed 20, overrode 13, null 47.

**Departures from the pre-work entry:**
1. **Contested primary ranges.** Each kept record also stores `primary_contested_with`: the other ranges that hold the same bug just as much (its other half, or the same mistake on a parallel code path). The brief's report asks for clear vs contested ranges, and inferring that from note wording would be unreliable. Clear in 48 of 80 kept cases, contested in 32. New open question Q62: does a finding on a contested range count as a strict hit? Decide before Step 6.
2. **Evidence sources beyond PRs and issues**, all read-only:
   - the local upstream clones, for three cases (a changelog, and two code checks at a commit);
   - one GitHub security advisory, via a GET request.
3. **Issue links written as full URLs.** `fetch_evidence.py` now recognises same-repo issue links written as full URLs, and the 23 affected cases were re-fetched.
4. **Re-check and corrections.** After the session break, the first 8 cases were re-checked with no change. Corrections were appended as new records (the latest record counts):
   - one category, for consistency: a dropped keyword argument is `type-or-contract`;
   - one primary range, moved to where the maintainer's review comment put the bug;
   - two notes: one unverified claim removed, one compat note brought to the `external-compat` prefix.
5. **Suspicious clean case that is likely buggy.** Clean case `3fe0fe03cd5c9e75` (click) introduced the eager `default=True` → `flag_value` substitution behind issues #3111 and #3121. SZZ missed it because the fixes changed code that had been moved, so blame did not reach this commit. It stays a clean case, marked suspicious, as the rules say.

### Why I am making this change
The owner asked for an evidence-grounded labelling pass on the dev split, with a label report.

### Alternatives I considered
- Leave out the contested-range field and report coverage from the notes.
- Drop the likely-buggy clean case.

### Reasons I rejected each alternative
- The note wording is not a reliable signal, and Step 6 needs the ranges anyway.
- The rules say suspicious clean cases stay clean, with a note.

### Trade-offs I am accepting
- The labels are LLM-made from human-written evidence, with a single annotator. This is stated in Benchmark and in the report.
- `o` was used for every compat-only fix, including compat with older supported versions (pytest ≤ 6.1.2, Python 3.8). Those are environment issues the reviewer cannot see from the diff.

### What could go wrong
- Category choices between `type-or-contract` and `control-flow` are the least certain; the alternative category is in each note.
- One kept case, `2109faa46125df3d`, is arguably not-a-bug: the maintainer had chosen the old behaviour deliberately before agreeing to change it.

### How this affects other components
- **Benchmark:** the dev labels exist; the labels section is rewritten for the Q61 amendment.
- **Metrics:** strict recall depends on Q62. Category-correct recall uses the kept dev cases.
- **Label Noise:** measured.

---

## M3: Q62 recall tiers, owner verification sample, metric caveats: pre-work
**Date**: 2026-10-03
**File(s) affected**:
- Created: `evals/benchmark/verify_sample.py`, `evals/benchmark/data/verification_sample.md`, `tests/test_verify_sample.py`
- Edited: `docs/vault/03 Reliability/Metrics.md`, `docs/vault/03 Reliability/Benchmark.md`, `docs/vault/06 Risks/Benchmark Leakage.md`, `docs/vault/06 Risks/Label Noise.md`, `docs/vault/07 Progress/Open Questions.md` (Q62 closed), Current Status, Session Log, 00 Brief

### What I am changing
Owner decisions, 2026-10-03:
1. **Q62.** Strict recall counts a finding on *any range recorded as holding the bug*: the primary range plus `primary_contested_with`. Step 6 reports three tiers, and runs the chance baseline against all three:
   - lenient: any auto-labelled range;
   - strict: any bug-holding range;
   - primary-only: the primary range.
2. **Verification sample.** `verify_sample.py` selects 25 kept buggy dev cases with a recorded seed, and writes `verification_sample.md` for the owner to mark by hand.
   - Stratified across repos and across the four macro-eligible categories, with at least one case from each small category.
   - The owner's three borderline cases are added regardless of the selection: `2109faa4`, `c06100e3`, `0f097b6d`.
   - Each case shows the diff the reviewer sees, the assigned labels and the recorded evidence links, with agree/disagree boxes for validity, category and primary range, and a note field.
   - The script also scores the ticked file, so the agreement rates come from a run, not a hand count.
   - The owner's verdicts are not filled in.
3. **Metrics caveats.**
   - Every false-positive rate is reported with the clean-case noise floor (3 of 41 suspicious, 7.3%).
   - Whenever macro recall is reported, the per-category counts are reported with it.
   - The SZZ code-movement limitation is recorded in Benchmark Leakage.

### Why I am making this change
Owner decisions before Steps 4–7.

### Alternatives I considered
1. Count the three borderline cases inside the 25.
2. Proportional allocation across the four macro categories.

### Reasons I rejected each alternative
1. They were chosen because they are hard, so including them would bias the agreement rate. They are reported separately, and `2109faa4` (a kept case) is excluded from the stratified pool so that it is not drawn twice.
2. Proportional allocation would give `error-handling` and `concurrency-or-async` one or two cases each, too few to say anything per category. Each macro category gets at least 3, and the rest is allocated by size.

### Trade-offs I am accepting
- The 25 cases are stratified, not a simple random sample, so per-field agreement on them is not exactly a population estimate. The rates are reported with raw counts and the per-category breakdown.

### What could go wrong
- Regenerating the sample after the owner has started would overwrite the verdicts. The script refuses to overwrite a file that has any ticked box unless `--force` is passed.

### How this affects other components
- **Metrics:** three recall tiers; FP rates carry the noise floor; macro recall carries per-category counts.
- **Benchmark:** gains the verification statement once the verdicts are in.

---

## M3: Q62 recall tiers, owner verification sample, metric caveats: completion
**Date**: 2026-10-03
**File(s) affected**:
- As in the pre-work entry above.
- Also edited: `evals/benchmark/fetch_evidence.py`, `evals/benchmark/data/labels_human.jsonl` (evidence lists only), `docs/vault/08 Results/label-report-dev-2026-10-03.md` (regenerated; only the label-file hash changed).

### What I am changing
**Results:**
- **Verification sample:** 25 kept dev cases.
  - By category: type-or-contract 6, control-flow 5, concurrency-or-async 4, error-handling 4, one each from null-or-none-handling, off-by-one-or-boundary, arithmetic-or-numeric, resource-leak, CWE-20 and CWE-400.
  - By repo: anyio 7, fastapi 7, click 5, marshmallow 3, rich 3 (each within one case of its share of kept cases).
  - Plus the 3 borderline cases, in their own section.
  - Seed 20261003. `python -m evals.benchmark.verify_sample --score` computes agreement per field and per section. Nothing is ticked.
- **Metrics:** three recall tiers; the noise-floor and category-count rules. Q62 closed.
- **Benchmark Leakage:** the SZZ code-movement limit.

**Departures from the pre-work entry:**
1. **Template link removed from evidence.** anyio's PR template names issue #123 as a changelog example, and the fetcher had linked it as evidence for 19 anyio cases.
   - The fetcher now skips code blocks and HTML comments in PR bodies, plus a per-repo list of template example numbers. One PR body kept the example in prose.
   - The 19 cases were re-fetched read-only. Their records' `evidence` lists were corrected in place: only that URL was removed, which was checked record by record against the committed file. No label changed.
   - The issue played no part in any judgement.
2. **First allocation draft wrong.** It re-applied the proportional split on each pass and gave type-or-contract 9 of 19 slots. It was replaced by a single largest-remainder pass, with a test.

### Why I am making this change
Owner decisions before Steps 4–7. The evidence links shown to the owner must be real evidence.

### Alternatives I considered
Append corrected records for the 19 cases instead of editing the evidence lists in place.

### Reasons I rejected each alternative
The label decisions did not change. Appending would only have duplicated 19 records to fix metadata, and the append-only rule exists to keep label history.

### Trade-offs I am accepting
The label file's hash changed. The label report and the sample record the new hash.

### What could go wrong
Some evidence lists may still contain a link the labeller read but did not need. Only #123 was found by the check over all 143 cases.

### How this affects other components
- **Metrics:** Step 6 implements three tiers and both caveats.
- **Benchmark:** the verification statement and agreement rates follow the owner's verdicts.

---

## M3: owner verification of the dev labels recorded
**Date**: 2026-10-03
**File(s) affected**:
- `evals/benchmark/data/verification_sample.md` (ticked)
- `evals/benchmark/label_report.py` (section 9: owner verification, with a Wilson lower bound)
- `tests/test_label_report.py`
- `docs/vault/03 Reliability/Benchmark.md`, `docs/vault/06 Risks/Label Noise.md`, the label report note, Current Status, Session Log, 00 Brief

### What I am changing
- The verdicts are the project owner's, given after reviewing all 28 cases: agree on every field. The agent entered the ticks at the owner's instruction.
- All `agree` boxes were ticked, and the file header says how the verdicts were entered.
- Score (`verify_sample --score`): 25/25 on validity, category and primary range; borderline cases 3/3 on validity, 1/1 on category and primary range.
- Benchmark now states that the labels are LLM-assigned from human-written upstream evidence and were verified by the project owner on a stratified 25-case sample, with these rates.

### Why I am making this change
The owner's verdicts gate Steps 4–7.

### Alternatives I considered
Report the bare 100%.

### Reasons I rejected each alternative
25/25 has a 95% Wilson lower bound of 86.7%, so the bound is reported next to the rate.

### Trade-offs I am accepting
The verdicts are a blanket agreement with no per-case notes. That is recorded as such.

### What could go wrong
The 20 dropped cases outside the borderline set were not sampled.

### How this affects other components
- **Benchmark:** the label-quality statement is complete.
- **Steps 4–7:** unblocked.

---

## M3 Steps 4–8: cache, runner, metrics, baseline run (ADR-024): pre-work
**Date**: 2026-10-03
**File(s) affected**:
- Created:
  - `docs/vault/04 Decisions/ADR-024 Eval runs pin a single provider and model.md`
  - `evals/cache.py`, `evals/runner.py`, `evals/metrics.py`, `evals/report.py`
  - tests for each
  - `evals/results/<run_id>/` (results.jsonl, summary.json, run.json)
  - `docs/vault/08 Results/baseline-dev-<date>.md`
- Edited:
  - code: `app/llm.py`, `app/graph/baseline.py`, `app/config.py`, `.gitignore`
  - docs: `docs/flow.md` (section 9, call graph); Metrics, Eval Harness, Benchmark, LLM Client, Free Tier Throughput, Open Questions; Current Status, Session Log, 00 Brief, 00 Index
  - `evals/benchmark/data/verification_sample.md` (verdict wording, owner's pre-step)

### What I am changing
**ADR-024:**
- `Settings` gains `eval_provider` / `eval_model`, defaulting to `groq` / `openai/gpt-oss-120b`.
- `app/llm.py` gains `PinnedLLM`:
  - fields: provider, model, and an optional cache implementing a small `ResponseCache` protocol (`key`, `get`, `put`);
  - `complete(..., pinned=)`: with `pinned` set, one attempt on that model, never the cascade.
  - The provider's error message is carried on `LLMError.detail`, so the runner can tell a per-minute limit from a daily one.
- `LLMResponse` gains `reasoning` (the model's thinking, needed in M5).
- `run_baseline_review(diff, pr_metadata, llm=None)` passes `llm` through. `BaselineResult` gains `error_type`, `error_status` and `error_detail`, so the runner can classify failures without a second code path. The worker is unchanged.

**Step 4, cache** (`evals/cache.py`):
- SQLite, `evals/.cache/responses.db`.
- Key: SHA-256 over provider, model, the full prompt messages, temperature and max_tokens.
- Stores the full `LLMResponse` as JSON.
- `--cache-only` mode raises `CacheMiss` on a miss, before any provider call.

**Step 5, runner** (`evals/runner.py`):
- **Scored set:** kept buggy plus all clean.
- **Pacing:** a sliding 60-second token window with an estimated request size of prompt + `max_tokens`, kept under 8,000 tokens/minute.
- **Rate limits:** 429 responses get exponential backoff, honouring `retry-after`. A daily limit (provider message mentions "per day", TPD or RPD), or repeated per-minute failures, checkpoints and exits with code 3; `--resume` continues.
- **Provider limits:** 413, or a provider message about request size or context length, means `failed: provider-limit`.
- **`--dry-run`:** builds every prompt with `build_messages()` (the review path's own function) and estimates tokens with LiteLLM's `token_counter` (a local tokenizer, no network). The estimate is calibrated against actual `prompt_tokens` after the run.
- **Run directory:** `evals/results/<run_id>/` holds `run.json` (config and git SHA), `results.jsonl` (incremental) and `summary.json`.

**Step 6, metrics** (`evals/metrics.py`):
- **Location match:** a finding in the same file whose line range overlaps the labelled range widened by ±3 lines (Q23); exact-line matching uses no margin. This settles the overlap-or-containment point Metrics left open. Overlap was chosen because a finding pointing at any part of the buggy code should count, and the chance baseline's one-line findings get the same rule.
- **Recall:** three tiers × two modes. Failed cases count as misses, and the failure counts are reported.
- **Other metrics:** micro and macro recall (floor ≥5, with per-category counts), precision (strict and lenient, location-only and category-correct), and false positives on clean cases (overall, per size bucket, per repo, with the noise floor). Every rate carries a Wilson 95% interval and k/n.
- **Chance baseline:** first changed line of each hunk, as `type-or-contract`.

**Step 7:** the run, a `--cache-only` rerun, and `evals/report.py` writing the vault report. Committed only if the dry run shows it fits one day's budget; otherwise stop and report.

### Why I am making this change
Owner brief for M3 Steps 4–8 and the ADR-024 decision.

### Alternatives I considered
1. Put the cache inside `app/` behind a setting.
2. Retry rate limits inside `complete()`.

### Reasons I rejected each alternative
1. The cache is an eval concern. The app only defines the protocol, so production never touches SQLite.
2. Pacing and budget decisions need run-level state (token window, checkpoint), which belongs to the runner. `complete()` in pinned mode stays a single attempt.

### Trade-offs I am accepting
- Token estimates use a local tokenizer that may differ from the model's own. The dry run states the method and the report compares the estimate with actual counts.

### What could go wrong
- Groq's daily budget (200K tokens) may not cover 121 cases plus reasoning output in one day. The dry run decides.
- Groq may count the requested `max_tokens` toward its per-minute limit. Pacing assumes it does (prompt + `max_tokens`).

### How this affects other components
- **LLM Client:** a pinned single-model mode, with production unchanged.
- **Eval Harness, Metrics:** built.
- **Free Tier Throughput:** first measured run.

---

## M3 Steps 4–6 built; stopped at the dry run
**Date**: 2026-10-03
**File(s) affected**:
- As in the pre-work entry above, except `evals/report.py`, `evals/results/` and the baseline report (not created: Step 7 did not start).
- Also edited: `docs/vault/06 Risks/Free Tier Throughput.md`, `docs/vault/02 Architecture/LLM Client.md`; created `tests/test_eval_harness.py`.

### What I am changing
**Built:** ADR-024 (pinned mode), `evals/cache.py`, `evals/runner.py`, `evals/metrics.py`, 36 tests (174 in all), `docs/flow.md` section 9 and the call-graph rows.

**Dry run** (`python -m evals.runner --split dev --dry-run`; tiktoken `cl100k_base` estimates):
- 121 scored cases (80 kept buggy, 41 clean).
- Prompt tokens: max 1,703, total 125,635 (63% of Groq's 200K/day).
- Largest request: 3,751, against the 8,000 ceiling (prompt + `max_tokens` 2,048). Every case fits.
- Daily budget: the run fits one day only if completions average ≤615 tokens. Worst case (full `max_tokens` every time): 373,443 (187%).
- Eight earlier production `gpt-oss-120b` generations in Langfuse (read-only API) averaged 822 completion tokens (93–1,257), so the expected total is about 225K.

**Per the brief, I stopped after the dry run. No LLM call was made.** Q64 asks the owner how to proceed.

**Departures from the brief:**
1. **Neutral PR title for every eval case.** The production prompt includes the PR title, and each case's real commit subject (for example "🐛 Fix …") would tell the reviewer what the bug is, and would separate buggy from clean cases by title. The diff is unchanged.
2. **Run-ID clash fixed.** Two runs started in the same second (a run, then its `--cache-only` rerun) got the same ID; a numeric suffix now separates them. A test caught it.
3. **Latency kept from the original call.** The cache stores each call's latency, so a `--cache-only` rerun reproduces the same latency metrics instead of near-zero ones.

### Why I am making this change
The owner's brief requires stopping when the run does not fit one day's budget.

### Alternatives I considered
Start the run anyway and let `--resume` carry it into a second day.

### Reasons I rejected each alternative
The brief says to stop and report. A two-day run is one of the Q64 options, for the owner to choose.

### Trade-offs I am accepting
`evals/report.py` is not written yet. It will be written against a real `summary.json` once Step 7 starts.

### What could go wrong
- The `cl100k_base` estimates differ from gpt-oss's own tokenizer. The runner records estimated and actual prompt tokens per case, so the first real run calibrates them.

### How this affects other components
- **Eval Harness, Metrics:** built; status in-progress.
- **Free Tier Throughput:** dry run measured.
- **Open Questions:** Q63 (run-to-run variance), Q64 (run budget, blocking Step 7).

---

## M3 Step 7: Q64 two-day baseline run, case shuffle, model check, leak scan: pre-work
**Date**: 2026-10-03
**File(s) affected**:
- Created: `evals/benchmark/leak_scan.py`, `evals/report.py`, tests, `evals/results/<run_id>/`, `docs/vault/08 Results/baseline-dev-<date>.md`
- Edited: `evals/runner.py`, `evals/metrics.py`; Eval Harness, Benchmark, Open Questions (Q64 closed), Free Tier Throughput; Current Status, Session Log, 00 Brief

### What I am changing
Owner decisions, 2026-10-03:
1. **Q64: option 1.** The dev baseline runs over two days with `--resume`, all on the pinned model, configuration unchanged. No workaround for the daily limit.
2. **Shuffled order.** Cases run in an order shuffled with a fixed seed recorded in `run.json`, so a day boundary cannot line up with a repo, category or buggy/clean grouping. A resumed run rebuilds the same order from the recorded seed.
   - Each record gets `started_at`, `finished_at` and the `session` (runner invocation) it ran in.
   - `summary.json` lists the cases per session and per UTC date.
3. **Model consistency.** Each record keeps the model identifier the provider returned. The summary reports the identifiers per session and whether they were identical across sessions; a difference goes into the report's Caveats.
4. **Leak scan, no LLM calls.** `evals/benchmark/leak_scan.py` scans the `-` lines of every scored eval diff (the fix's own lines, which the reviewer sees as removed) for:
   - issue or PR references (`#\d+`, GitHub URLs);
   - the words fix, bug, workaround, regression, hack, "see issue".

   It reports counts and case IDs. No case is changed; the owner decides after seeing the numbers.
5. **Neutral PR title,** recorded as a known difference between eval and production. Eval cases get one neutral PR title to prevent label leakage, so the eval measures diff-only review. Production passes the real title, so production performance may differ.

### Why I am making this change
Owner decisions on Q64 and additions before the baseline run.

### Alternatives I considered
Record days by local date only.

### Reasons I rejected each alternative
Groq's daily budget is not tied to a calendar day, so the runner session is the meaningful unit. Both the session and the UTC date are recorded.

### Trade-offs I am accepting
The run's order differs from case-ID order. The order is reproducible from the seed.

### What could go wrong
- The daily stop may fall mid-way through Groq's window. The runner stops on the first daily-limit response and does not retry, per the owner's instruction.
- Langfuse receives the eval traces, which is acceptable for public diffs (Q49).

### How this affects other components
- **Eval Harness:** the run order and provenance fields.
- **Benchmark:** the leak-scan result is recorded.

---

## M3 Step 7: dev baseline run: completion
**Date**: 2026-10-03 (recorded 2026-10-04)
**File(s) affected**: as in the Step 7 pre-work entry, plus `docs/vault/09 External Facts.md` and the results in `evals/results/dev-20261003T122301Z-86166c4/` (baseline) and `dev-20261003T132348Z-86166c4/` (cache-only rerun)

### What I am changing
**Results:**
- **Run shape:**
  - 121 cases in one session, 12:23–13:23 UTC;
  - 122 provider calls (one per-minute retry);
  - 219,611 tokens.
- **Provenance:** pinned `groq/openai/gpt-oss-120b`, 100% of answered cases, model ID identical throughout.
- **Statuses:** 119 success, 1 partial, 1 parse failure.
- **Reproducibility:** the `--cache-only` rerun gave identical reviewer and chance metrics with 0 provider calls.
- **Metrics:**
  - strict category-correct recall 41/80 (51.2%, CI 40.5–61.9%);
  - precision 75/109 (68.8%);
  - clean FP 17/41 (41.5%).
- **The chance baseline beat the reviewer on location recall** (strict 76/80 vs 64/80). That prompted the owner's metric redesign.

**Departures:**
1. **One day, not two.** Q64 planned two days, but no daily-limit response came. The documented 200K tokens/day did not bind, and External Facts now marks that limit as unverified.

### Why I am making this change
Recording the outcome of Step 7.

### Alternatives I considered
None.

### Reasons I rejected each alternative
Not applicable.

### Trade-offs I am accepting
Single run; variance is not measured (Q63).

### What could go wrong
The undocumented daily-limit behaviour may change.

### How this affects other components
Metrics redesign follows (ADR-025).

---

## M3: metric redesign (ADR-025), McNemar, leak masking, diagnostics: pre-work
**Date**: 2026-10-04
**File(s) affected**:
- Created:
  - `docs/vault/04 Decisions/ADR-025 Detection-first metrics.md`
  - tests
  - a new run directory (masked rerun)
  - `docs/vault/08 Results/baseline-dev-2026-10-04.md`
- Edited:
  - code: `evals/metrics.py`, `evals/runner.py`, `evals/report.py`
  - docs: Metrics, Benchmark, Eval Harness, Open Questions, Results README, the 2026-10-03 report (marked superseded), `docs/flow.md`, Current Status, Session Log, 00 Brief

### What I am changing
Owner brief, 2026-10-04.

**1. Diagnostics** (no LLM):
- **Base rate:** the share of each buggy case's changed lines inside its bug-holding ranges ±3.
- **Strict-location misses:** classified by cause.
- **Coordinate check:** every finding is classified as new-side, old-side-only or outside.

Result before any change, from cached results:
- base rate: mean 81.2%, median 100%, 46 of 80 cases at 100%;
- misses: 10 no findings, 1 parse failure, 2 on changed lines outside the window, 3 outside the shown lines;
- coordinates: 98 of 109 findings use new-file lines, 7 cite removed lines by old-file number, 4 are outside the diff.

That is not a systematic offset, so the work continues. The old-side convention gap is recorded as Q65 for the owner, since fixing it means changing the review path.

**2. ADR-025, detection-first headline**, computed for the reviewer and the chance baseline:
- detection rate (TPR) and clean flag rate (FPR);
- Youden's J = TPR − FPR, with a Newcombe hybrid-score 95% interval (difference of two independent Wilson intervals);
- category-correct recall, whose chance value equals the majority-class rate;
- precision;
- strict location recall at ±0, ±1 and ±3, with ±3 labelled non-discriminating on this benchmark.

**3. Paired comparisons:** an exact McNemar test (two-sided binomial on the discordant pairs b, c) for comparing two runs on the same cases: detection, strict category-correct recall, and clean flags.

**4. Leak masking:**
- **The rule:** a versioned diff transform, `mask-issue-refs-v1`, applied by the runner to the `-` lines of every case.
  - `#123` becomes `#N`;
  - GitHub issue and PR URLs become `<issue-link>`;
  - the comment text is kept.
- **Why:** masking removes the memorisation route (the model may know what a specific upstream issue was about) while keeping the realistic signal (a comment explaining the code).
- **Which cases:** it changes the prompt of only the cases that contain such references. A full run then hits the cache for every unchanged case and calls the model only for the masked ones.
- **Provenance:** `run.json` records the transform, and the report states that the baseline includes the masked rerun.
- **Unchanged cases:** the leak-scan cases whose removed lines contain words only (fix, workaround) have nothing to mask. Their prompts are unchanged, so their cached results stand.

**5. Clean false-positive diagnostic:** category, severity, repo and size of every finding on a clean case, and which suspicious clean cases were flagged.

**6. Re-report:**
- a new `baseline-dev-2026-10-04.md`;
- the 2026-10-03 report kept and marked superseded.

### Why I am making this change
Location matching cannot separate the reviewer from chance on this benchmark (chance strict location recall 95%).

### Alternatives I considered
1. Edit the case files (`dev.jsonl`) to mask the references.
2. Use a Wald interval for J.

### Reasons I rejected each alternative
1. The case files stay the upstream truth. A versioned eval-time transform is recorded per run and applies identically to the holdout later.
2. Wald intervals behave badly near 0 and 1; Newcombe's method builds on the Wilson intervals already used everywhere.

### Trade-offs I am accepting
- Masking changes prompts, so the masked cases are fresh samples. Part of any change there is run-to-run variance (Q63, not yet measured).

### What could go wrong
- With ~7 masked cases, before/after differences will not be statistically meaningful. They are reported with counts.

### How this affects other components
- **Metrics:** new headline.
- **Benchmark:** the masking rule is recorded.
- **Eval Harness:** the diff transform is recorded in `run.json`.
- **Review path:** unchanged; Q65 is the owner's decision.

---

## M3: metric redesign (ADR-025), McNemar, leak masking, diagnostics: completion
**Date**: 2026-10-04
**File(s) affected**:
- As in the pre-work entry.
- Also: `docs/vault/09 External Facts.md`, the `evals/diagnostics.py` module, and the run directory `evals/results/dev-20261004T085157Z-ad2fc7d/`.

### What I am changing
**Results:**
- **Base rate:** mean 81.2%, median 100%, 46 of 80 cases at 100%. Location matching is non-discriminating, and Metrics says so with the number.
- **Strict-location misses** (16):
  - 10 no findings;
  - 1 parse failure;
  - 2 findings that cite removed lines by old-file number;
  - 2 on changed lines outside ±3;
  - 1 outside the diff.
- **Coordinates:** 98 of 109 findings are new-side, 7 old-side only, 4 outside. That is no systematic offset, so this is not the stop condition. The convention gap is Q65 for the owner.
- **Headline** (masked baseline):

  | Metric | Reviewer | Chance |
  |---|---|---|
  | J | 0.435 (0.257 to 0.586) | 0.000 |
  | Strict category-correct | 41/80 | 34/80 (majority class) |
  | Precision | 74/108 | 94/243 |
  | Clean flag rate | 17/41 | 41/41 |
- **Location tolerance:** strict location at ±0 / ±1 / ±3 is reviewer 45, 54, 64 of 80 against chance 60, 60, 76.
- **Masking:**
  - 7 cases changed (6 buggy, 1 clean); the 4 other leak-scan cases had nothing to mask;
  - exactly 7 LLM calls, 114 cache hits;
  - 9 leak-scan buggy cases: detection 9/9 → 8/9, category-correct 3/9 → 3/9 (the other 71: 60/71 and 38/71);
  - McNemar against the first run: detection b = 1, c = 0, p = 1.0; category b = 1, c = 1, p = 1.0; clean flags 0/0.
- **Clean false positives:**
  - 20 findings on 17 cases;
  - by category: type-or-contract 11, control-flow 4, off-by-one 2, others 1 each;
  - by severity: medium 14, high 3, low 3;
  - by size: 16–30 lines 6 of 8 flagged, 1–5 lines 7 of 17;
  - suspicious clean cases flagged: `3350b7f5` and `3fe0fe03`.

**Departures:**
1. **7 cases rerun, not 11.** The brief named the 11 leak-scan cases. Only 7 have references to mask, so the other 4 prompts are unchanged and their cached answers stand. Calling them again would only sample model variance.
2. **The baseline is a full run, not a patched results file.** It ran with the cache: unchanged cases are byte-identical cache hits, and the masked ones are fresh calls. `run.json` records `diff_transform` and every record carries `diff_masked`, so the report states which cases were rerun.
3. **Old summary left as committed.** The first run's `summary.json` is kept as written; reports recompute older summaries in memory.
4. **One push with a failing test.** I pushed `ad2fc7d` with the report test still failing, because I had run only a subset of the tests. The next commit fixes it.

### Why I am making this change
Owner brief, 2026-10-04.

### Alternatives I considered
Stop at the coordinate finding.

### Reasons I rejected each alternative
The brief's stop condition is a coordinate bug (a systematic mismatch). The finding is a 6% convention gap confined to removed lines, and it does not affect the detection-first headline, so the work continued and Q65 records it for the owner.

### Trade-offs I am accepting
The masked cases are single fresh samples (Q63).

### What could go wrong
Q65 also affects production comment placement, and is undecided.

### How this affects other components
- **Metrics:** headline changed.
- **Benchmark:** masking rule.
- **Open Questions:** Q65.

---

## M3: Q63 noise floor, Q65 fix (ADR-026, baseline v2), sensitivity line, Q25 targets: pre-work
**Date**: 2026-10-04
**File(s) affected**:
- Created: `docs/vault/04 Decisions/ADR-026 Numbered diffs and validated output.md`, two run directories (the v1 rerun and v2), `docs/vault/08 Results/baseline-dev-<date>-v2.md`
- Edited:
  - code: `app/graph/baseline.py`, `app/github/diff.py`, `evals/metrics.py`, `evals/report.py`, tests
  - docs: `docs/flow.md`; Finding Schema, Metrics, Success Metrics, Ablation Table, Open Questions (Q63, Q65, Q25 closed); the earlier reports (marked superseded); Results README; Current Status, Session Log, 00 Brief

### What I am changing
Owner decisions, 2026-10-04.

**1. Q63, run-to-run variance.**
- The dev baseline is rerun with `--no-cache` as a new run, with the same configuration and the same review-path code. `app/`, `evals/runner.py` and `evals/cache.py` are identical between v1's commit `ad2fc7d` and HEAD; the git SHA differs only through docs and report code.
- Exact McNemar against v1 on detection, strict category-correct recall and clean flags, listing the cases that changed.
- The disagreement counts become the **ablation noise floor**. An improvement counts only if it is McNemar-significant against the previous row **and** its disagreement count exceeds what two identical runs produce.

**2. Q65 fix, ADR-026, baseline v2.** Four changes to the review path:
- **Numbered diff in the prompt:** every context and added line is prefixed with its new-file line number, and removed lines are marked `-` with no number.
- **Prompt rule:** findings use new-file line numbers; a finding about removed code anchors to the nearest new-file line in the same hunk.
- **Line validation:** a finding whose line falls outside every hunk's new-file range is dropped and counted as `invalid_line`.
- **One retry on validation failure:** malformed JSON or an invalid element gets one retry, with the errors fed back. Retries are counted; a second failure goes to `parse_errors` as before. The tokens and cost of both calls are summed.

Production gets the same review path (one code path). The v2 run uses the pinned model with the cache on; the prompt changes, so every case is a fresh call.

**3. Sensitivity line,** in every report: clean flag rate, precision and J recomputed excluding the 3 clean cases marked suspicious during labelling, before any run. The headline stays on the full frozen set.

**4. Q25 targets,** measured on the final holdout run:

| Metric | Target |
|---|---|
| Youden's J | ≥ 0.60 |
| Clean flag rate | ≤ 20% |
| Precision | ≥ 80% |
| Strict category-correct recall | ≥ 60% |
| Cost per PR (list-price estimate) | ≤ 3× baseline |
| p95 latency | ≤ 30 s |

Each claimed improvement must be McNemar-significant against the previous ablation row on dev and exceed the run-to-run noise. Targets are ambitions; the final results page states which were met.

**5. Report:** v1, the v1 rerun and v2 side by side, with the noise floor, the v1→v2 McNemar result, the sensitivity line and the targets table. Earlier reports are kept as superseded.

### Why I am making this change
Owner decisions on Q63, Q65 and Q25, and on the suspicious clean cases.

### Alternatives I considered
Map old-side line numbers after the fact instead of numbering the diff.

### Reasons I rejected each alternative
The owner chose numbering in the prompt, so the model reads line numbers rather than computing them. It also fixes production comment placement at the source.

### Trade-offs I am accepting
- The numbered prompt is longer (more tokens per case).
- Retries add calls on cases that fail validation.

### What could go wrong
- Groq's daily budget: two full runs today. If the limit binds, the runner checkpoints and the owner gets the resume command.
- Changing the prompt changes behaviour beyond line numbers. Q63's noise floor tells signal from variance.

### How this affects other components
- **Review Graph / baseline:** new prompt, numbered diff, validation and retry. Production comments now get correct line numbers.
- **Metrics:** noise-floor rule, sensitivity line, targets.
- **Ablation Table:** starts with v1 → v2.
