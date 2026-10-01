---
type: progress
status: in-progress
tags: [progress]
related:
  - "[[Session Log]]"
  - "[[Open Questions]]"
  - "[[00 Index]]"
---

# Current Status

**Phase:** M2 done (baseline reviewer verified live). Next: M3 (benchmark).
**Last updated:** 2026-10-01

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

**Next**
- Q54: list the category taxonomy in the prompt before the M3 benchmark
- Q20: verify benchmark repo candidates; Q37b: security taxonomy
- Q47 (TestClient), Q48 (large PRs), Q49 (secrets in traces), Q52b (stable webhook URL)
