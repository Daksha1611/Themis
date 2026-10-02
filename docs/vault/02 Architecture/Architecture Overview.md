---
name: Architecture Overview
description: "Diagram and summary of the review path and the reliability layer, marking what is built and what is planned."
type: component
status: in-progress
tags: [component]
related:
  - "[[Webhook Service]]"
  - "[[Job Queue]]"
  - "[[Context Builder]]"
  - "[[Review Graph]]"
  - "[[Finding Schema]]"
  - "[[Precision Filter]]"
  - "[[Guardrails]]"
  - "[[GitHub Integration]]"
  - "[[LLM Client]]"
  - "[[Storage]]"
  - "[[Tracing]]"
  - "[[Operational Monitoring]]"
  - "[[Eval Harness]]"
---

# Architecture Overview

Two halves: the **review path** (reviews PRs) and the **reliability layer** (measures and protects review quality).

```mermaid
flowchart LR
    GH[GitHub PR event] --> WH[Webhook Service<br/>FastAPI]
    WH -->|enqueue job| Q[Job Queue<br/>arq + Redis]
    Q --> W[Worker]
    W --> CB[Context Builder<br/>tree-sitter + Qdrant]
    GI[GitHub Integration<br/>app/github] -->|diff| CB
    CB -->|ReviewContext| GS[Guardrails<br/>sanitize]
    GS --> RG
    subgraph RG[Review Graph - LangGraph]
        BP[Bug pass] --> M[Merge / de-duplicate]
        SP[Security pass] --> M
    end
    RG -->|Findings, no confidence| GV[Guardrails<br/>validate]
    GV --> PF[Precision Filter<br/>sets confidence]
    PF -->|filtered Findings| GI
    GI -->|review comments| GH2[GitHub PR]
    RG --> LLM[LLM Client<br/>LiteLLM]
    LLM --> CAS[Free-tier cascade<br/>Groq → Gemini → Mistral → OpenRouter]
    W --> DB[(Storage<br/>PostgreSQL)]
    GH2 -.outcome signals.-> GI
    GI -.raw signals.-> DB
    DB -.pilot outcome labels.-> PF

    subgraph REL[Reliability layer]
        T[Tracing<br/>Langfuse cloud]
        B[Benchmark<br/>dev / holdout] --> EH[Eval Harness]
        EH --> MET[Metrics]
        MET --> CI[CI Quality Gate]
        MET --> DM[Drift Monitoring]
        MET --> AB[Ablation Table]
        EH --> RJ[(results.jsonl<br/>+ response cache)]
        CI -.main-branch history.-> EDB[(Eval database)]
    end
    RG -.traced.-> T
    EH -.runs full review path.-> W
```

**Review path:** [[Webhook Service]] → [[Job Queue]] → [[Context Builder]] → [[Guardrails]] (sanitize) → [[Review Graph]] → [[Guardrails]] (validate) → [[Precision Filter]] → [[GitHub Integration]] (post comments). [[Finding Schema]] is the data contract between them. [[LLM Client]] and [[Storage]] support the path.

**Reliability layer:** [[Tracing]], [[Benchmark]], [[Eval Harness]], [[Metrics]], [[CI Quality Gate]], [[Drift Monitoring]], [[Ablation Table]].

**Deferred to post-v1:** [[Operational Monitoring]] (Prometheus + Grafana).

## Built so far (M1–M2) versus planned
The diagram is the target design. What runs today (details in `docs/flow.md`):

[[Webhook Service]] → [[Job Queue]] worker → [[GitHub Integration]] (installation token, diff fetch) → [[Review Graph]] as a single baseline pass over the raw diff → [[GitHub Integration]] (post review) → [[Storage]] (`review_runs` row). [[LLM Client]] (four-provider cascade), [[Finding Schema]] (`Finding`, `ReviewResult`) and [[Tracing]] are built.

| Part | State |
|---|---|
| Webhook Service, LLM Client | built |
| Job Queue, GitHub Integration, Finding Schema, Storage, Tracing | built for the M2 path; later parts planned |
| Review Graph | baseline pass built; LangGraph bug and security passes planned |
| Context Builder, Guardrails, Precision Filter | planned |
| Outcome signals (dotted lines) | planned |
| Benchmark | in progress (M3) |
| Eval Harness, Metrics, CI Quality Gate eval job, Drift Monitoring, Ablation Table | planned; `ci.yml` (lint, types, tests, vault check) runs today |
