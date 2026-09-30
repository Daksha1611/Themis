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

**Phase:** M2 in progress. Code complete and tested; live end-to-end blocked on three owner actions.
**Last updated:** 2026-09-30

**Done (M2)**
- Alembic initialised; startup bootstrap removed; two migrations verified on a fresh database; migrations run on container start ([[Storage]])
- LLM client via LiteLLM → OpenRouter with cost tracking ([[LLM Client]])
- Final `Finding` / `ReviewResult` schema, `confidence` vs `raw_llm_confidence` ([[Finding Schema]])
- Diff fetch, baseline review pass, PR review posting with out-of-diff summary ([[GitHub Integration]], [[Review Graph]])
- Tracing reworked to Langfuse best practices and audited against real traces in Langfuse cloud ([[Tracing]])
- 38 tests; ruff, mypy clean
- Live run verified up to the diff fetch: real App token, real bot comment, real `review_runs` row, real Langfuse trace

**Blocked (owner actions)**
- Q50: add **Contents: Read** to the GitHub App
- Q51: raise the OpenRouter key's spending limit
- Q52: restart the tunnel and update the App's webhook URL

**Next**
- After the three actions: rerun the live checks (buggy PR, clean PR), then mark M2 done
- Q47 (TestClient migration), Q48 (large PRs), Q49 (secrets in traces)
