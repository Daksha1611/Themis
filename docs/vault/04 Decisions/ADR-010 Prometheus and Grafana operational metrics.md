---
name: ADR-010 Prometheus and Grafana operational metrics
description: "Superseded for v1: Prometheus and Grafana operational metrics, deferred to post-v1."
type: decision
status: superseded
tags: [decision]
related:
  - "[[Operational Monitoring]]"
  - "[[Prometheus]]"
  - "[[Grafana]]"
  - "[[Tracing]]"
  - "[[Hosting]]"
  - "[[Prior Art]]"
  - "[[Langfuse]]"
  - "[[Scope Creep]]"
---


# ADR-010 Prometheus and Grafana operational metrics

> **Superseded for v1 (2026-09-29).** Deferred to post-v1 stretch goals ([[Non-Goals]]).

## Context
[[Tracing]] (Langfuse) covers LLM calls, not the health of the running service: queue depth, job latency, webhook and worker errors. Proposed from [[Prior Art]].

## Decision (original)
[[Prometheus]] collects operational metrics from the running service; [[Grafana]] visualises them. See [[Operational Monitoring]].

## Alternatives considered
- Langfuse only: it does not measure service health.

## Why superseded
[[Langfuse]] already provides latency, cost, and token metrics, covering most of what these dashboards would show. Adding Prometheus and Grafana for v1 means:
- two additional Compose services
- a non-trivial worker instrumentation problem (Q40): an arq worker has no HTTP server, so it needs either a side server or a Pushgateway, with `prometheus_client` multiprocess-mode gotchas
- dashboard build work

This overlaps heavily with existing Langfuse coverage and is the kind of scope addition the [[Scope Creep]] risk note warns against.

**Status:** superseded for v1. Deferred to post-v1 stretch goals.

## If reinstated
Scope must be limited to four panels (review throughput, error rate, p95 latency, cost per PR) and one alert (webhook failure rate).
