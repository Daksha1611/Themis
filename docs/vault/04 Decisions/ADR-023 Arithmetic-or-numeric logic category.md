---
name: ADR-023 Arithmetic-or-numeric logic category
description: "Decision: add the arithmetic-or-numeric logic category, with precedence rules shared by prompt, Glossary and benchmark labels."
type: decision
status: accepted
tags: [decision]
related:
  - "[[ADR-019 Logic bug taxonomy]]"
  - "[[Finding Schema]]"
  - "[[Glossary]]"
  - "[[Benchmark]]"
  - "[[Metrics]]"
---

# ADR-023 Arithmetic-or-numeric logic category

Amends [[ADR-019 Logic bug taxonomy]] (decides Q55).

## Context
ADR-019 had no category for arithmetic errors. In a live check (2026-10-01) the model filed both divide-by-zero bugs under `error-handling`. Without one rule applied the same way everywhere, category-correct recall measures definitional disagreement instead of detection.

## Decision
Add the logic category **`arithmetic-or-numeric`**: wrong arithmetic, division by zero, float precision, and overflow where Python can overflow.

**Precedence rules**, applied identically in three places: `app/taxonomy.py` (`PRECEDENCE_RULES`, and so the review prompt), the [[Glossary]], and the benchmark labelling rules (`evals/benchmark/labeling.py`):
- Arithmetic operators (+ - * / // % **) used wrongly -> arithmetic-or-numeric. Comparisons at a range edge (< vs <=) -> off-by-one-or-boundary.
- A computation that can divide by zero -> arithmetic-or-numeric. A ZeroDivisionError that is caught or handled wrongly -> error-handling.
- Overflow is scoped to what Python can actually overflow: floats (inf/nan), fixed-width types (numpy, struct, ctypes), and size limits. Python ints do not overflow.
- Float precision errors -> arithmetic-or-numeric.

## Alternatives considered
- Keep seven categories and file divide-by-zero under `error-handling`: hides arithmetic mistakes inside a category about exception handling.

## Consequences
- 8 logic categories; the prompt lists them with the precedence rules.
- **Few benchmark cases:** a keyword pass over the candidate commits found about 4 numeric ones, so this category's recall is reported with raw counts only ([[Metrics]]).
- No labeled data existed before this change, so nothing needed relabeling.
