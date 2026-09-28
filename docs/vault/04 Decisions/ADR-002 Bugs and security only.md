---
type: decision
status: done
tags: [decision]
related:
  - "[[Scope]]"
  - "[[Non-Goals]]"
  - "[[Review Graph]]"
  - "[[Finding Schema]]"
  - "[[Scope Creep]]"
---

# ADR-002 Bugs and security only

**Status:** accepted

## Context
The core promise is high precision and low noise ([[Vision]]).

## Decision
v1 findings are limited to logic bugs and security issues. No style or formatting comments.

## Alternatives considered
- Style/lint comments: listed as a non-goal ([[Non-Goals]]).

## Consequences
- [[Review Graph]] has exactly two passes: logic bugs and security.
- [[Finding Schema]] categories are limited to these two.
