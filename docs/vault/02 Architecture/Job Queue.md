---
type: component
status: planned
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
- Orchestrate the job: [[Context Builder]] → [[Guardrails]] (sanitize) → [[Review Graph]] → [[Guardrails]] (validate) → [[Precision Filter]] → comment posting by [[GitHub Integration]]

**Inputs:** review jobs from the [[Webhook Service]].
**Outputs:** a completed review run (findings posted to the PR; `ReviewResult` recorded in [[Storage]]).

**Planned code location:** `app/worker/` (queue consumer, job orchestration).

**Dependencies:** [[arq]], [[Redis]]. Decision: [[ADR-003 arq + Redis queue]].
