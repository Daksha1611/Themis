---
name: Prior Art
description: "The course PR-reviewer project Themis was compared against, and what was taken from it or rejected."
type: project
status: done
tags: [project]
related:
  - "[[Vision]]"
  - "[[Scope]]"
  - "[[Non-Goals]]"
  - "[[Open Questions]]"
---

# Prior Art

## Advanced AI GitHub PR Code Reviewer (course project)
Source: https://www.krishnaik.in/project/lfnm (public listing only; course content is paid).

**What it is:** an event-driven GitHub PR reviewer. GitHub webhooks feed five FastAPI microservices (Gateway, Webhook, Orchestrator, Reviewer, Learner) connected by Celery + Redis, with PostgreSQL. Parallel LangGraph agents cover static analysis, security (OWASP Top 10), architecture, and code style, on GPT-4o-mini. A Learner service mines merged PRs for style patterns. Observability: Prometheus, Grafana, Langfuse. GitHub App auth with JWT.

## Comparison

| | Course project | Themis |
|---|---|---|
| Review scope | Static analysis, security, architecture, style | Logic bugs + security only ([[Scope]]) |
| Quality measurement | None stated | [[Benchmark]], [[Metrics]], [[CI Quality Gate]] |
| Noise control | None stated | [[Precision Filter]] |
| Repo context | Not stated | [[Context Builder]] (tree-sitter + Qdrant hybrid) |
| Prompt injection | Not stated | [[Guardrails]] |
| Model | Fixed GPT-4o-mini | Free-tier provider cascade, configurable via [[LLM Client]]; compared by [[Drift Monitoring]] |
| Evidence | Feature list | [[Ablation Table]] |
| Services | 5 microservices | Webhook + worker |

## What Themis takes from it
Approved and recorded as ADRs:
- OWASP Top 10 security taxonomy: [[ADR-009 OWASP Top 10 security taxonomy]] (later superseded by [[ADR-022 CWE Top 25 security taxonomy]])
- Operational metrics with Prometheus + Grafana: [[ADR-010 Prometheus and Grafana operational metrics]] (later superseded for v1; post-v1 stretch goal)
- Learning from real usage, scoped to precision (not style): [[ADR-011 Finding outcomes as precision-filter labels]]

## What Themis deliberately does not take
- Style checker and the style-learning Learner service: style is a [[Non-Goals|non-goal]].
- Architecture reviewer: outside v1 scope.
- Five-service split and Celery: [[ADR-003 arq + Redis queue]] already covers async work with less operational weight.
