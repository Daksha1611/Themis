---
name: Current Status
description: "Where the project stands: current milestone, what is done, what is next."
type: progress
status: in-progress
tags: [progress]
related:
  - "[[Session Log]]"
  - "[[Open Questions]]"
  - "[[00 Index]]"
---

# Current Status

**Phase:** M3 in progress. Steps 2–3 built (238 cases; SZZ clean rule; frozen splits). **Waiting for the owner's dev labelling pass** before Steps 4–7.
**Last updated:** 2026-10-02 (vault audit and hardening)

New sessions start with [[00 Brief]].

**Done (M2)**
- Alembic-managed schema; startup bootstrap gone ([[Storage]])
- Free-tier four-provider LLM cascade ([[ADR-021 Free-tier four-provider LLM cascade]], [[LLM Client]])
- Final `Finding` / `ReviewResult` schema with `confidence` vs `raw_llm_confidence` ([[Finding Schema]])
- Diff fetch, baseline pass, PR review posting ([[GitHub Integration]], [[Review Graph]])
- Langfuse tracing audited against real traces: provider, tokens, cost and model thinking captured ([[Tracing]])
- 46 tests; ruff, mypy, CI green
- **Live test, 2026-10-01** on `Daksha1611/themis-test-repo`, delivered by GitHub through the tunnel:
  - PR #2 (planted bugs): 3 line comments, one per bug (off-by-one, missing None check, divide-by-zero); Groq `openai/gpt-oss-120b`; 6.1 s
  - PR #3 (clean change): "no issues found" comment; Groq; 2.5 s

**Done (M3 so far)**
- CWE Top 25 (2024) security taxonomy ([[ADR-022 CWE Top 25 security taxonomy]]); ADR-009 superseded
- Categories constrained in prompt and validated in `Finding` (Q54); 73 tests
- Test repo cleaned (all PRs closed, branches deleted)
- Repo verification table ([[Benchmark]]); leakage date distribution ([[Benchmark Leakage]])

**Done (vault audit and hardening, 2026-10-02)**
- Vault corrected against the code and the live system: superseded decisions, component notes, statuses, stack versions, open-question numbering, metric definitions
- [[00 Brief]] (mandatory first read) and [[09 External Facts]] (outside-world facts with verification dates, re-checked live on 2026-10-02)
- `scripts/check_vault.py` with 21 tests; `vault-check` CI job. 94 tests in all
- OpenRouter's free model returned 429 (upstream rate limit) on 2026-10-02; the other three providers answered

**Next**
- Owner decision: final repo list (Q20), size-filter scope (Q56), arithmetic category (Q55)
- Then M3 Steps 2–8: mine, build cases, cache, runner, metrics, baseline dev report
- Q47 (TestClient), Q48 (large PRs), Q49 (secrets in traces), Q52b (stable webhook URL)
