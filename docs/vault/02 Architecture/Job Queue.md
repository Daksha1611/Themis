---
type: component
status: planned
tags: [component]
related:
  - "[[Webhook Service]]"
  - "[[Context Builder]]"
  - "[[Review Graph]]"
  - "[[Precision Filter]]"
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
- Orchestrate the job: [[Context Builder]] → [[Review Graph]] → [[Precision Filter]] → comment posting

**Inputs:** review jobs from the [[Webhook Service]].
**Outputs:** a completed review run (findings posted to the PR; run recorded in [[Storage]]).

**Planned code location:** `app/worker/` (queue consumer, job orchestration).

**Dependencies:** [[arq]], [[Redis]]. Decision: [[ADR-003 arq + Redis queue]].
