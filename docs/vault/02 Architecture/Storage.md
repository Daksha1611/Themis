---
name: Storage
description: "PostgreSQL storage of review runs via SQLAlchemy and Alembic; where eval results and outcome signals go."
type: component
status: in-progress
tags: [component]
related:
  - "[[Job Queue]]"
  - "[[Eval Harness]]"
  - "[[Finding Schema]]"
  - "[[Precision Filter]]"
  - "[[GitHub Integration]]"
  - "[[CI Quality Gate]]"
  - "[[PostgreSQL]]"
  - "[[SQLAlchemy]]"
  - "[[Alembic]]"
  - "[[Docker]]"
  - "[[ADR-011 Finding outcomes as precision-filter labels]]"
  - "[[ADR-012 Alembic for schema migrations]]"
---

# Storage

**Purpose:** persist review runs; later, finding outcomes and the CI gate's eval history.

**Responsibilities**
- **Built:** store one row per review in the `review_runs` table: `repo`, `pr_number`, `head_sha`, `status` (`success` | `partial` | `failed`; M1 rows say `dummy`), `started_at`, `completed_at`, `cost_usd` (list-price estimate), `error`, `finding_count`, `raw_finding_count`, `prompt_tokens`, `completion_tokens`, `model`, `diff_chars`, `diff_truncated`. **`model` holds `<provider>/<model>`** (for example `groq/openai/gpt-oss-120b`), so the row records which cascade provider answered. The full `ReviewResult` is not stored here; it is the Langfuse trace output ([[Tracing]]).
- **Planned:** store finding-outcome signals from [[GitHub Integration]]. Raw signals are stored separately from the derived label ([[ADR-011 Finding outcomes as precision-filter labels]]).
- **Planned (M7):** the dedicated eval database, never production. It holds **run-level summary metrics only**: one row per eval run (precision, recall, cost, latency, git SHA, split, timestamp), small and persistent, consumed by the [[CI Quality Gate]] to compare a PR against main's last recorded run. **Case-level results** (one record per benchmark case, large, regenerable) are not stored here: they live in `results.jsonl` files written by the [[Eval Harness]].

**Inputs:** review runs from the [[Job Queue]] worker; later, outcome signals from [[GitHub Integration]] and run-level eval summaries from the [[Eval Harness]] (for the [[CI Quality Gate]]).
**Outputs:** stored records; later, outcome labels for the [[Precision Filter]].

**Code location:** `app/storage/` ([[ADR-012 Alembic for schema migrations]]):
- `models.py` ([[SQLAlchemy]])
- `repository.py`
- `migrations/` ([[Alembic]]): initialised in M2. Revisions: `75a08c2847ca` (review_runs, M1 columns), `37e292134510` (M2 LLM and finding columns). `alembic upgrade head` runs when the api and worker containers start, under a Postgres advisory lock.

**Dependencies:** [[PostgreSQL]], [[Docker]]. Neon free tier is an option ([[ADR-018 Paid VPS over free tier hosting]]).
