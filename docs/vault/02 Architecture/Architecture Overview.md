---
type: component
status: planned
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
    LLM --> OR[OpenRouter]
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
        EH --> EDB[(Eval database)]
    end
    RG -.traced.-> T
    EH -.runs full review path.-> W
```

**Review path:** [[Webhook Service]] → [[Job Queue]] → [[Context Builder]] → [[Guardrails]] (sanitize) → [[Review Graph]] → [[Guardrails]] (validate) → [[Precision Filter]] → [[GitHub Integration]] (post comments). [[Finding Schema]] is the data contract between them. [[LLM Client]] and [[Storage]] support the path.

**Reliability layer:** [[Tracing]], [[Benchmark]], [[Eval Harness]], [[Metrics]], [[CI Quality Gate]], [[Drift Monitoring]], [[Ablation Table]].

**Deferred to post-v1:** [[Operational Monitoring]] (Prometheus + Grafana).
