---
name: Job Queue
description: "The arq worker that runs each review job, its steps and its retry rules."
type: component
status: in-progress
tags: [component]
related:
  - "[[Webhook Service]]"
  - "[[Context Builder]]"
  - "[[Guardrails]]"
  - "[[Review Graph]]"
  - "[[Precision Filter]]"
  - "[[GitHub Integration]]"
  - "[[Storage]]"
  - "[[arq]]"
  - "[[Redis]]"
  - "[[ADR-003 arq + Redis queue]]"
---

# Job Queue

**Purpose:** decouple webhook receipt from the slow review work.

**Responsibilities**
- Hold review jobs enqueued by the [[Webhook Service]]
- Run a worker that consumes review jobs
- Orchestrate the job.
  - **Built (M2):** installation token → diff fetch ([[GitHub Integration]]) → baseline review ([[Review Graph]]) → post findings, or the "no issues" comment ([[GitHub Integration]]) → store the run ([[Storage]]). Details: `docs/flow.md` section 2.
  - **Planned:** [[Context Builder]] → [[Guardrails]] (sanitize) → [[Review Graph]] → [[Guardrails]] (validate) → [[Precision Filter]] → comment posting by [[GitHub Integration]].

**Inputs:** review jobs from the [[Webhook Service]].
**Outputs:** findings posted to the PR; one `review_runs` row in [[Storage]]; the full `ReviewResult` ([[Finding Schema]]) as the Langfuse trace output ([[Tracing]]). The `ReviewResult` itself is not stored in Postgres.

**Retries and failures**
- arq `max_tries = 5`. A GitHub rate limit (403/429 with `Retry-After`) raises `arq.Retry(defer=Retry-After)`.
- Any other failure after the installation token is obtained posts an error comment on the PR and stores a `failed` row, with no retry, so the LLM call is never repeated.
- An installation-token failure stores a `failed` row and re-raises; no PR comment is possible without a token.

**Code location:** `app/worker/queue.py` (`WorkerSettings`, worker startup and shutdown, the API's queue client), `app/worker/job.py` (`handle_review_job`).

**Dependencies:** [[arq]], [[Redis]]. Decision: [[ADR-003 arq + Redis queue]].
