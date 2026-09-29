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
