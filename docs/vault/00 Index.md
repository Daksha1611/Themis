---
type: project
status: in-progress
tags: [project]
related:
  - "[[Vision]]"
  - "[[Architecture Overview]]"
  - "[[Current Status]]"
  - "[[Open Questions]]"
---

# Themis — Index

> An AI code reviewer that weighs the evidence before it speaks.

Start here: [[Current Status]] · [[Open Questions]] · [[Architecture Overview]] · [[Themis Map.canvas|Themis Map]] (visual map)

Outside the vault: `docs/flow.md` (what the code does), `docs/decision.md` (why each change was made).

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

## 03 Reliability
- [[Tracing]]
- [[Benchmark]]
- [[Eval Harness]]
- [[Metrics]]
- [[CI Quality Gate]]
- [[Drift Monitoring]]
- [[Ablation Table]]

## 04 Decisions
- [[ADR-001 Python-only v1]]
- [[ADR-002 Bugs and security only]]
- [[ADR-003 arq + Redis queue]]
- [[ADR-004 Qdrant hybrid search]]
- [[ADR-005 LiteLLM via OpenRouter]]
- [[ADR-006 Langfuse tracing]]
- [[ADR-007 dev-holdout benchmark split]]
- [[ADR-008 Encoder classifier as precision filter]]

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

## 06 Risks
- [[Eval Cost]]
- [[Hosting]]
- [[Label Noise]]
- [[Scope Creep]]

## 07 Progress
- [[Current Status]]
- [[Session Log]]
- [[Open Questions]]

## 08 Results
- [[08 Results/README|Results README]]
