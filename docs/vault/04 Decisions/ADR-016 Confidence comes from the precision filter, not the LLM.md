---
name: ADR-016 Confidence comes from the precision filter, not the LLM
description: "Decision: a finding's confidence comes from the precision filter, never from the LLM."
type: decision
status: accepted
tags: [decision]
related:
  - "[[Finding Schema]]"
  - "[[Precision Filter]]"
  - "[[Review Graph]]"
  - "[[LLM Client]]"
---

# ADR-016 Confidence comes from the precision filter, not the LLM

## Context
Every [[Finding Schema|Finding]] has a `confidence` field. LLM self-reported confidence is poorly calibrated.

## Decision
`confidence` is a float from 0.0 to 1.0, **produced by the [[Precision Filter]], never by the LLM**.

## Alternatives considered
- LLM self-reported confidence: poorly calibrated.

## Consequences
- The [[Review Graph]] emits findings without a confidence value; the Precision Filter sets it.
- Separating generation (LLM) from judgment (classifier) is central to the project's thesis.
