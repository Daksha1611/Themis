---
type: progress
status: in-progress
tags: [progress]
related:
  - "[[Current Status]]"
  - "[[Guardrails]]"
  - "[[Precision Filter]]"
  - "[[Storage]]"
  - "[[CI Quality Gate]]"
  - "[[Benchmark]]"
---

# Open Questions

Items the spec leaves unspecified or contradictory. Resolve before building the affected part.

## Spec / document conventions
1. **decision.md location.** The spec says "create `docs/decision.md` at the repo root (not inside the vault)". `docs/decision.md` is not the repo root. Used `docs/decision.md` (matches the session rules). Same for `docs/flow.md`.
2. **Frontmatter `tags: [#component]`.** In YAML `#` starts a comment, so this would parse as an empty list. Used `tags: [component]` (Obsidian adds the `#`).
3. **Frontmatter `related: [[a]], [[b]]`.** Unquoted, YAML reads this as nested lists, not links. Used a list of quoted wikilinks so Obsidian recognises them.
4. **Decision status.** Frontmatter `status` allows planned / in-progress / done, but ADRs need "accepted". Used `status: done` in frontmatter and **Status: accepted** in the body.
5. **Type for hub and results notes.** `00 Index` and `Results README` have no matching type. Used `project` and `reliability`.
6. **Meaning of `status` for risk and stack notes.** Used `planned` for all.

## Architecture gaps
7. **Guardrails placement.** Before the [[Review Graph]], after it, or both? What happens on detection (skip review, strip content, flag the PR)?
8. **Comment posting has no component note.** `app/github/` owns GitHub App auth, diff fetch, and comment posting, but none of the nine components owns posting. Add a "GitHub Integration" component?
9. **[[Storage]] code location.** Not in the planned repo structure.
10. **[[Tracing]] and [[Drift Monitoring]] code locations.** Not in the planned repo structure.
11. **Langfuse deployment.** Self-hosted or cloud? It is not in the docker-compose service list.
12. **Repo index lifecycle.** When is a repo indexed into Qdrant (on install, per PR, incrementally)?
13. **Embedding model** for hybrid search, and how BM25 is implemented, are not specified.
14. **Context Builder output format** is not specified.
15. **ReviewResult fields** are not specified.
16. **Finding severity and confidence scales** are not specified.

## Precision filter
17. **Score threshold** is not specified.
18. **Base encoder model** is not specified.
19. **Training labels.** Where do the labels for `training/label_findings.py` come from, and does training data overlap the benchmark (leakage into holdout)?

## Benchmark and metrics
20. **Which ~5 repos.** Not chosen.
21. **Split ratio** between dev and holdout.
22. **Clean PR source.** How clean PRs are selected.
23. **"Correct location" tolerance** for bug recall (exact line, or within the labeled range?).
24. **Injection resistance definition** and how `evals/injection/` cases are scored.
25. **Numeric targets** for [[Success Metrics]].
26. **Leakage** is described in the benchmark but not listed under Risks. Should it get its own risk note?

## Reliability layer
27. **CI gate thresholds** for precision and recall, and whether "drops" means versus the main branch or versus a fixed number.
28. **CI secrets and cost.** The eval gate needs an OpenRouter key in GitHub Actions; PRs from forks cannot access secrets.
29. **Drift monitoring schedule** and which providers/models to compare.
30. **Ablation Table split.** Dev or holdout?
31. **Public results page.** Where is it hosted?
32. **Lint and test tools** for `ci.yml` are not in the tech stack.

## Operations
33. **Hosting provider** is not chosen ([[Hosting]]).

## Proposals from prior art
From [[Prior Art]]. Not adopted; each needs approval and an ADR.

34. **OWASP Top 10 as the security-pass taxonomy.** Use OWASP Top 10 (or CWE IDs) as the `category` values for security findings in the [[Finding Schema]]. Makes security findings comparable and gives the benchmark a labeling vocabulary.
35. **Operational metrics (Prometheus + Grafana).** Queue depth, job latency, and error rates for the running app. Would be a new technology; overlaps partly with [[Tracing]].
36. **Learning from repo history, scoped to precision.** The course's Learner mines merged PRs for style. A Themis version could instead use which posted findings were resolved or dismissed as labels for the [[Precision Filter]] (ties to Q19). Must not become style learning.
