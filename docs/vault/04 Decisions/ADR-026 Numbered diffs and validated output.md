---
name: ADR-026 Numbered diffs and validated output
description: "Decision: the review prompt shows new-file line numbers on every diff line, findings must use them, findings outside every hunk are dropped, and an invalid response gets one retry with the errors fed back."
type: decision
status: accepted
tags: [decision]
related:
  - "[[Review Graph]]"
  - "[[Finding Schema]]"
  - "[[Metrics]]"
  - "[[ADR-025 Detection-first metrics]]"
---

# ADR-026 Numbered diffs and validated output

Owner decision, 2026-10-04 (closes Q65).

## Context
The baseline prompt showed a raw unified diff and never said which line numbers to use. The model had to compute new-file line numbers from hunk headers.

In the dev baseline, 98 of 109 findings used new-file lines, as labels and GitHub review comments do. But findings about removed code sometimes cited the removed lines by their **old-file** numbers: 7 findings, behind 2 strict-location misses. In production such a finding lands on the wrong line, or GitHub rejects it.

The model also sometimes invented category names (`logic-or-contract`), which failed validation and lost the whole finding.

## Decision
1. **Numbered diff.** The prompt renders the diff with each context and added line prefixed by its new-file line number. Removed lines are marked `-` and carry no number. File and hunk headers are kept. The model reads line numbers instead of computing them (`number_diff()` in `app/github/diff.py`).
2. **Prompt rule.** `line_start` and `line_end` are new-file line numbers shown in the diff. A finding about removed code anchors to the nearest numbered line in the same hunk.
3. **Line validation.** A finding whose start or end line falls outside every hunk's new-file range is dropped and counted (`invalid_line`), since GitHub would reject a comment there.
4. **One retry on validation failure.** If the response is not a JSON array, or any element fails validation (for example an invalid category), the model is asked once more with the validation errors fed back. Retries are counted; the tokens and cost of both calls are recorded; a second failure goes to `parse_errors` as before.

The same review path serves production and evals (one code path).

## Consequences
- **Baseline v2** is the first row change of the [[Ablation Table]] (v1 → v2, prompt hygiene). It is judged by McNemar against v1, interpreted against the run-to-run noise floor (Q63).
- Prompts are longer: the line-number prefixes add tokens.
- Some cases make two calls.
