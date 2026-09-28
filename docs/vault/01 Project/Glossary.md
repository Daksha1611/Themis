---
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

- **Finding**: one structured review result (file, line, category, severity, message, confidence). See [[Finding Schema]].
- **Logic bug / security issue**: the only two finding categories in v1.
- **Buggy PR**: a benchmark case created by reverting a bug-fix commit, labeled with the file and line range of the bug. See [[Benchmark]].
- **Clean PR**: a benchmark case with no known bug, used to measure false positives.
- **Dev split**: benchmark cases used for tuning and in CI.
- **Holdout split**: benchmark cases run only at milestones.
- **Leakage**: a benchmark case the model may have seen in training.
- **Bug recall**: share of seeded bugs flagged at the correct location. See [[Metrics]].
- **Comment precision**: share of posted comments that are correct. Headline metric.
- **Hybrid search**: retrieval combining BM25 (keyword) and embeddings (semantic). See [[Context Builder]].
- **Prompt injection**: instructions hidden in code comments, docstrings, or PR descriptions that try to steer the reviewer. See [[Guardrails]].
- **OWASP Top 10**: a standard list of the ten most critical web application security risk categories. Used as the category for security findings. See [[ADR-009 OWASP Top 10 security taxonomy]].
- **Finding outcome**: whether a posted finding was resolved or dismissed on the PR. Used as a precision-filter label. See [[ADR-011 Finding outcomes as precision-filter labels]].
- **Ablation**: measuring metrics while adding one component at a time. See [[Ablation Table]].
- **Drift**: change in review quality across LLM providers or model versions over time. See [[Drift Monitoring]].
- **p95 latency**: the latency that 95% of reviews finish within.
