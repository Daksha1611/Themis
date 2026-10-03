---
name: 00 Index
description: "Entry point of the vault: links to every note, grouped by section."
type: project
status: in-progress
tags: [project]
related:
  - "[[00 Brief]]"
  - "[[09 External Facts]]"
  - "[[Vision]]"
  - "[[Architecture Overview]]"
  - "[[Current Status]]"
  - "[[Open Questions]]"
---

# Themis — Index

> An AI code reviewer that weighs the evidence before it speaks.

Read first, every session: [[00 Brief]]. Then: [[Current Status]] · [[Open Questions]] · [[Architecture Overview]] · [[Themis Map.canvas|Themis Map]] (visual map)

Outside the vault: `README.md` (repo overview), `docs/flow.md` (what the code does), `docs/decision.md` (why each change was made).

## 01 Project
- [[Prior Art]]
- [[Glossary]]
- [[Non-Goals]]
- [[Scope]]
- [[Success Metrics]]
- [[Vision]]

## 02 Architecture
- [[Architecture Overview]]
- [[Webhook Service]]
- [[Job Queue]]
- [[Context Builder]]
- [[Review Graph]]
- [[Finding Schema]]
- [[Precision Filter]]
- [[Guardrails]]
- [[LLM Client]]
- [[Storage]]
- [[GitHub Integration]]

## 03 Reliability
- [[Tracing]]
- [[Benchmark]]
- [[Eval Harness]]
- [[Metrics]]
- [[CI Quality Gate]]
- [[Drift Monitoring]]
- [[Ablation Table]]
- [[Operational Monitoring]]

## 04 Decisions
- [[ADR-001 Python-only v1]]
- [[ADR-002 Bugs and security only]]
- [[ADR-003 arq + Redis queue]]
- [[ADR-004 Qdrant hybrid search]]
- [[ADR-005 LiteLLM via OpenRouter]]
- [[ADR-006 Langfuse tracing]]
- [[ADR-007 dev-holdout benchmark split]]
- [[ADR-008 Encoder classifier as precision filter]]
- [[ADR-009 OWASP Top 10 security taxonomy]]
- [[ADR-010 Prometheus and Grafana operational metrics]]
- [[ADR-011 Finding outcomes as precision-filter labels]]
- [[ADR-012 Alembic for schema migrations]]
- [[ADR-013 Langfuse cloud over self-hosting]]
- [[ADR-014 Incremental repo indexing]]
- [[ADR-015 Local embeddings and Qdrant native hybrid search]]
- [[ADR-016 Confidence comes from the precision filter, not the LLM]]
- [[ADR-017 Dev-split-only training data for the precision filter]]
- [[ADR-018 Paid VPS over free tier hosting]]
- [[ADR-019 Logic bug taxonomy]]
- [[ADR-020 M1 runtime dependencies]]
- [[ADR-021 Free-tier four-provider LLM cascade]]
- [[ADR-022 CWE Top 25 security taxonomy]]
- [[ADR-023 Arithmetic-or-numeric logic category]]
- [[ADR-024 Eval runs pin a single provider and model]]

## 05 Stack
- [[Python]]
- [[FastAPI]]
- [[arq]]
- [[Redis]]
- [[LangGraph]]
- [[LiteLLM]]
- [[OpenRouter]]
- [[Qdrant]]
- [[tree-sitter]]
- [[PostgreSQL]]
- [[Langfuse]]
- [[HuggingFace Transformers]]
- [[Pydantic]]
- [[Docker]]
- [[GitHub Actions]]
- [[Prometheus]]
- [[Grafana]]
- [[SQLAlchemy]]
- [[Alembic]]
- [[sentence-transformers]]
- [[ruff]]
- [[mypy]]
- [[pytest]]
- [[pytest-cov]]
- [[pytest-asyncio]]
- [[starlette]]
- [[Caddy]]
- [[httpx]]
- [[PyJWT]]
- [[pydantic-settings]]
- [[uvicorn]]
- [[psycopg]]
- [[Groq]]
- [[Gemini]]
- [[Mistral]]

## 06 Risks
- [[Benchmark Leakage]]
- [[Eval Cost]]
- [[Free Tier Throughput]]
- [[Hosting]]
- [[Label Noise]]
- [[Scope Creep]]

## 07 Progress
- [[Current Status]]
- [[Session Log]]
- [[Open Questions]]

## 08 Results
- [[08 Results/README|Results README]]
- [[label-report-dev-2026-10-03]]

## 09 External Facts
- [[09 External Facts]]: outside-world facts that expire, with verification dates
