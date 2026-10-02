---
name: ADR-001 Python-only v1
description: "Decision: v1 reviews Python repositories only."
type: decision
status: accepted
tags: [decision]
related:
  - "[[Scope]]"
  - "[[Non-Goals]]"
  - "[[Context Builder]]"
  - "[[Benchmark]]"
  - "[[Scope Creep]]"
---

# ADR-001 Python-only v1

## Context
Themis must ship a trustworthy v1. Scope creep is the biggest project risk ([[Scope Creep]]).

## Decision
v1 reviews Python repositories only.

## Alternatives considered
- Multi-language support: deferred to a stretch goal, only after all milestones ship ([[Non-Goals]]).

## Consequences
- [[Context Builder]] only needs to chunk Python.
- [[Benchmark]] is mined from Python repos.
