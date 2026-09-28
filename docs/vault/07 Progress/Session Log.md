---
type: progress
status: in-progress
tags: [progress]
related:
  - "[[Current Status]]"
  - "[[Open Questions]]"
---

# Session Log

## 2026-09-28
**Done:** created the git repo, the knowledge vault (`docs/vault/`), `docs/decision.md`, and `docs/flow.md` from the approved spec. No application code.
**Next:** approval of the planning docs; resolve [[Open Questions]].
**Blockers / questions:** see [[Open Questions]].

## 2026-09-28 (2)
**Done:** planning docs approved. Added the [[Themis Map.canvas|Themis Map]] canvas (data-flow map of every component and reliability note), graph view colour groups by folder (local setting), and the [[Prior Art]] note comparing Themis with a course PR-reviewer project.
**Next:** resolve [[Open Questions]], including proposals 34–36.
**Blockers / questions:** none new beyond Open Questions.

## 2026-09-28 (3)
**Done:** accepted prior-art proposals 34–36 as ADR-009 (OWASP Top 10 security taxonomy), ADR-010 (Prometheus + Grafana operational metrics), ADR-011 (finding outcomes as precision-filter labels). Added [[Operational Monitoring]], [[Prometheus]], [[Grafana]]; updated affected component, reliability, risk, and map notes.
**Next:** resolve [[Open Questions]] 1–33 and 37–43.
**Blockers / questions:** new questions 37–43.

## 2026-09-29
**Done:** recorded the answers to Open Questions 1–43. Added ADR-012 to ADR-019, [[GitHub Integration]], [[Benchmark Leakage]], and stack notes for SQLAlchemy, Alembic, sentence-transformers, ruff, mypy, pytest, pytest-cov, and Caddy. Rewrote ADR-011 as a pilot. Switched ADR frontmatter to `status: accepted`. Added a root README with the dev-split-only training rule. Settled four conflicts first: results page deploys via GitHub Actions (not served from `docs/`); rule goes in a new root README; SQLAlchemy covered by ADR-012; CI and drift use a separate eval database.
**Next:** decide Q37 and Q41; choose benchmark repos (Q20).
**Blockers / questions:** Q20, Q25, Q37, Q41 open.
