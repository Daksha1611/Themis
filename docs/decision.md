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
