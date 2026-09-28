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
  - "[[LLM Client]]"
  - "[[Storage]]"
  - "[[Tracing]]"
  - "[[Eval Harness]]"
  - "[[Operational Monitoring]]"
---

# Architecture Overview

Two halves: the **review path** (reviews PRs) and the **reliability layer** (measures and protects review quality).

```mermaid
flowchart LR
    GH[GitHub PR event] --> WH[Webhook Service<br/>FastAPI]
    WH -->|enqueue job| Q[Job Queue<br/>arq + Redis]
    Q --> W[Worker]
    W --> CB[Context Builder<br/>tree-sitter + Qdrant]
    CB --> RG
    subgraph RG[Review Graph - LangGraph]
        BP[Bug pass] --> M[Merge / de-duplicate]
        SP[Security pass] --> M
    end
    RG -->|Findings| PF[Precision Filter<br/>encoder classifier]
    PF -->|filtered Findings| POST[Comment posting<br/>app/github]
    POST --> GH2[GitHub PR comments]
    RG --> LLM[LLM Client<br/>LiteLLM]
    LLM --> OR[OpenRouter]
    GR[Guardrails<br/>prompt-injection detection] -.placement TBD.- RG
    W --> DB[(Storage<br/>PostgreSQL)]
    GH2 -.finding outcomes.-> DB
    DB -.outcome labels.-> PF

    subgraph REL[Reliability layer]
        T[Tracing<br/>Langfuse]
        OM[Operational Monitoring<br/>Prometheus + Grafana]
        B[Benchmark<br/>dev / holdout] --> EH[Eval Harness]
        EH --> MET[Metrics]
        MET --> CI[CI Quality Gate]
        MET --> DM[Drift Monitoring]
        MET --> AB[Ablation Table]
    end
    RG -.traced.-> T
    WH -.metrics.-> OM
    W -.metrics.-> OM
    EH -.runs full review path.-> W
    EH --> DB
```

**Review path components:** [[Webhook Service]] → [[Job Queue]] → [[Context Builder]] → [[Review Graph]] → [[Precision Filter]] → comment posting. [[Finding Schema]] is the data contract between them. [[Guardrails]], [[LLM Client]], and [[Storage]] support the path.

**Reliability layer:** [[Tracing]], [[Operational Monitoring]], [[Benchmark]], [[Eval Harness]], [[Metrics]], [[CI Quality Gate]], [[Drift Monitoring]], [[Ablation Table]].

Where Guardrails runs and which component owns comment posting are not specified. See [[Open Questions]].
