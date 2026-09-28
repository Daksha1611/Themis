---
type: component
status: planned
tags: [component]
related:
  - "[[Context Builder]]"
  - "[[Review Graph]]"
  - "[[Precision Filter]]"
  - "[[GitHub Integration]]"
  - "[[Metrics]]"
  - "[[Python]]"
---

# Guardrails

**Purpose:** stop hidden instructions in the reviewed code from steering the reviewer.

Runs at **two points**, with different jobs.

## Pre-graph: sanitize
- Strip or neutralise instruction-like text found in code comments, docstrings, and the PR description
- Wrap all untrusted content in explicit delimiters
- State in the prompt that delimited content is data to be reviewed, never instructions to follow

## Post-graph: validate
Drop any finding showing signs the model followed injected instructions:
- findings that reference the PR description
- findings that praise the code
- findings that request approval

## On detection
- **Never skip the review.** Review anyway using the sanitized input.
- Add one comment (posted by [[GitHub Integration]]) noting that suspicious instruction-like content was detected.
- Silently skipping is the worst outcome: it gives the attacker exactly what they wanted.
- The run records `guardrail_triggered` in its `ReviewResult`.

**Inputs:** the `ReviewContext` from the [[Context Builder]] (sanitize); findings from the [[Review Graph]] (validate).
**Outputs:** a sanitized `ReviewContext` to the [[Review Graph]]; validated findings to the [[Precision Filter]].

**Planned code location:** `app/guardrails/`. Adversarial test PRs in `evals/injection/`.

Measured by injection resistance in [[Metrics]].
