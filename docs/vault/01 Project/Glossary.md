---
name: Glossary
description: "Project terms, and what each frontmatter status value means per note type."
type: project
status: done
tags: [project]
related:
  - "[[Metrics]]"
  - "[[Benchmark]]"
  - "[[Context Builder]]"
  - "[[Guardrails]]"
---

# Glossary

## Note frontmatter
Every note has `name` (its filename), a one-line `description`, `type`, `status`, `tags` and `related`. Stack (`tech`) notes also have `version`, read from the installed package or image, never from memory; `version: not installed` is allowed only while the note is `planned`. `scripts/check_vault.py` enforces all of this in CI.

## Note `status` values
| Note type | `planned` | `in-progress` | `done` |
|---|---|---|---|
| project, component, reliability, progress | not started | partly built, or ongoing | built or complete |
| tech | not installed | installed, not yet used by the code | installed and in use |
| risk | no mitigation in place | partly mitigated | mitigated |

Decision notes use `accepted` \| `superseded` instead.

## Terms

- **Finding**: one structured review result (file, line range, category, subcategory, severity, message, suggestion, confidence, raw_llm_confidence). See [[Finding Schema]].
- **Logic bug / security issue**: the only two finding categories in v1.
- **Buggy PR**: a benchmark case created by reverting a bug-fix commit, labeled with the file and line range of the bug. See [[Benchmark]].
- **Clean PR**: a benchmark case with no known bug, used to measure false positives.
- **Dev split**: benchmark cases used for tuning and in CI.
- **Holdout split**: benchmark cases run only at milestones.
- **Leakage**: a benchmark case the model may have seen in training.
- **Bug recall**: share of seeded bugs with a finding at the labeled location (±3 lines) and in the correct category. See [[Metrics]].
- **Comment precision**: share of findings that land on a labeled bug; on clean PRs every finding is a false positive. Headline metric. See [[Metrics]].
- **Hybrid search**: retrieval combining sparse keyword vectors and dense embeddings, fused with Reciprocal Rank Fusion (RRF). See [[Context Builder]].
- **ReviewContext / ReviewResult**: the Context Builder's output (planned) and the record of one review run (built). See [[Finding Schema]].
- **Matched pair**: the same diff with and without an injected instruction, used to measure injection resistance.
- **Prompt injection**: instructions hidden in code comments, docstrings, or PR descriptions that try to steer the reviewer. See [[Guardrails]].
- **CWE Top 25**: MITRE's list of the 25 most dangerous software weaknesses. The Python-reachable subset of the 2024 edition is the security category set. See [[ADR-022 CWE Top 25 security taxonomy]].
- **Finding outcome**: whether a posted finding was validated (code near the line changed later on the PR) or dismissed (thread resolved with no change, or a negative maintainer reaction). A pilot label source for the precision filter. See [[ADR-011 Finding outcomes as precision-filter labels]].
- **Ablation**: measuring metrics while adding one component at a time. See [[Ablation Table]].
- **Drift**: change in review quality across LLM providers or model versions over time. See [[Drift Monitoring]].
- **p95 latency**: the latency that 95% of reviews finish within.
