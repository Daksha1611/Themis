---
type: progress
status: in-progress
tags: [progress]
related:
  - "[[Current Status]]"
  - "[[Benchmark]]"
  - "[[Success Metrics]]"
  - "[[ADR-009 OWASP Top 10 security taxonomy]]"
  - "[[ADR-010 Prometheus and Grafana operational metrics]]"
---

# Open Questions

## Still open
- **Q20. Specific benchmark repos.** Selection criteria are recorded in [[Benchmark]]; the repo list is not chosen.
- **Q25. Numeric targets.** Deferred until baseline numbers exist ([[Success Metrics]]).
- **Q37. Security taxonomy: OWASP Top 10 (2021) or CWE Top 25?** Awaiting decision ([[ADR-009 OWASP Top 10 security taxonomy]]).
- **Q41. Fate of ADR-010.** Recommended: supersede for v1. Awaiting decision ([[ADR-010 Prometheus and Grafana operational metrics]]).

## Resolved (2026-09-29)

### Document conventions
1. decision.md and flow.md live in `docs/`. Kept.
2. `tags: [type]` without `#`. Kept.
3. `related:` as a list of quoted wikilinks. Kept.
4. Decision notes use `status: accepted | superseded`; status values per type are in the [[Glossary]].
5. `00 Index` is `project`; Results README is `reliability`. Kept.
6. Risk and stack notes use `planned`. Kept.

### Architecture
7. Guardrails run twice: sanitize before the graph, validate after; never skip a review → [[Guardrails]]
8. New component owns App auth, diff fetch, comment posting → [[GitHub Integration]]
9. `app/storage/` with SQLAlchemy models and Alembic migrations → [[ADR-012 Alembic for schema migrations]]
10. Tracing in `app/observability/`; drift in `evals/drift/` plus a scheduled workflow → [[Tracing]], [[Drift Monitoring]]
11. Langfuse cloud, free tier → [[ADR-013 Langfuse cloud over self-hosting]]
12. Index on install, incrementally per PR, manually on demand → [[ADR-014 Incremental repo indexing]]
13. Local sentence-transformers embeddings; Qdrant native sparse vectors with RRF → [[ADR-015 Local embeddings and Qdrant native hybrid search]]
14. Context Builder outputs a Pydantic `ReviewContext` → [[Context Builder]], [[Finding Schema]]
15. `ReviewResult` fields defined → [[Finding Schema]]
16. Severity enum; confidence 0.0–1.0 from the precision filter, never the LLM → [[ADR-016 Confidence comes from the precision filter, not the LLM]]

### Precision filter
17. Threshold tuned by a precision-recall sweep, configurable; default ADR once real data exists → [[Precision Filter]]
18. Compare `microsoft/codebert-base` and `deberta-v3-small` as an ablation row → [[Precision Filter]], [[Ablation Table]]
19. Labels from dev-split runs only, enforced in code → [[ADR-017 Dev-split-only training data for the precision filter]]

### Benchmark and metrics
20. Selection criteria recorded; **repo list still open** → [[Benchmark]]
21. 60% dev / 40% holdout, stratified by repo and category → [[Benchmark]], [[ADR-007 dev-holdout benchmark split]]
22. Clean PRs: files with no bug fix for 6–12 months (heuristic), size-matched → [[Benchmark]]
23. Hit = within labeled range ±3 lines and correct category; exact-line accuracy secondary → [[Metrics]]
24. Injection resistance via matched pairs → [[Metrics]]
25. Shape of success recorded; **numbers still open** → [[Success Metrics]]
26. Own risk note → [[Benchmark Leakage]]

### Reliability layer
27. Gate compares against main's last run in a separate eval database; −3 pp precision / −5 pp recall → [[CI Quality Gate]]
28. Eval gate on in-repo branches only (50-case dev subset); forks run unit tests; full dev nightly → [[CI Quality Gate]]
29. Weekly drift on the fixed subset: models in use plus one cheaper, one stronger → [[Drift Monitoring]]
30. Ablation on holdout once at the end, with dev numbers alongside → [[Ablation Table]]
31. Results page deployed to GitHub Pages by an Actions build artifact from `evals/report.py` → [[Ablation Table]]
32. ruff, mypy, pytest (+ pytest-asyncio), pytest-cov → [[CI Quality Gate]]

### Operations
33. Small paid VPS with Docker Compose and Caddy → [[ADR-018 Paid VPS over free tier hosting]]

### Prior art (resolved 2026-09-28)
34. OWASP Top 10 taxonomy → [[ADR-009 OWASP Top 10 security taxonomy]]
35. Prometheus + Grafana → [[ADR-010 Prometheus and Grafana operational metrics]] (now pending Q41)
36. Outcome labels → [[ADR-011 Finding outcomes as precision-filter labels]]

### Raised by ADR-009 to ADR-011
37. OWASP Top 10 (2021) pinned; **CWE Top 25 reconsideration still open** → [[ADR-009 OWASP Top 10 security taxonomy]]
38. Logic bugs get a seven-category taxonomy → [[ADR-019 Logic bug taxonomy]]
39. `security-other` with a required subcategory; frequency tracked → [[Finding Schema]], [[Metrics]]
40. Worker metrics via side HTTP server or Pushgateway; only if ADR-010 survives → [[Operational Monitoring]]
41. **Still open** (see above)
42. Validated / dismissed signal definitions; raw signals kept separate from labels → [[ADR-011 Finding outcomes as precision-filter labels]]
43. Outcome labels reframed as a pilot, not a data engine → [[ADR-011 Finding outcomes as precision-filter labels]]
