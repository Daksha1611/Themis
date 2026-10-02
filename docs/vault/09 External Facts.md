---
name: 09 External Facts
description: "Register of outside-world facts that can expire (model IDs, free-tier limits, library versions, App permissions, CWE edition), with verification dates."
type: project
status: in-progress
tags: [project]
related:
  - "[[ADR-021 Free-tier four-provider LLM cascade]]"
  - "[[Free Tier Throughput]]"
  - "[[GitHub Integration]]"
  - "[[ADR-022 CWE Top 25 security taxonomy]]"
  - "[[LLM Client]]"
  - "[[00 Brief]]"
---

# External Facts

Facts that depend on the outside world and can change without notice. **Before relying on one, check its date. Re-verify anything older than 30 days, then update the row.** A row is only dated when the check was actually run. Facts read from documentation rather than a live call say so.

## LLM providers: model in use ([[ADR-021 Free-tier four-provider LLM cascade]])
| Provider | Model ID (`LLM_MODELS`) | Last verified | Result | How to re-verify |
|---|---|---|---|---|
| [[Groq]] | `openai/gpt-oss-120b` | 2026-10-02 | listed; test call answered in 1.1 s | `GET https://api.groq.com/openai/v1/models`, then one `litellm.acompletion(model="groq/<id>")` call |
| [[Gemini]] | `gemini-3.5-flash` | 2026-10-02 | listed; test call answered in 1.8 s | `GET https://generativelanguage.googleapis.com/v1beta/models?key=…`, then one call |
| [[Mistral]] | `codestral-2508` | 2026-10-02 | listed; test call answered in 0.5 s | `GET https://api.mistral.ai/v1/models`, then one call |
| [[OpenRouter]] | `qwen/qwen3.8-27b:free` | 2026-10-02 (listed) / 2026-10-01 (last answer) | listed, but **both test calls on 2026-10-02 returned 429: "temporarily rate-limited upstream"**. Last successful call 2026-10-01 | `GET https://openrouter.ai/api/v1/models`, then one call |

Known changes: `gemini-2.5-flash` was still listed but returned 404 (2026-10-01). Cerebras moved from a no-card free tier to a card-required trial (between planning and M2).

## Free-tier limits
| Provider | Limit | Source and date | How to re-verify |
|---|---|---|---|
| Groq, `openai/gpt-oss-120b` | 1,000 requests/day; **8,000 tokens/minute: the binding constraint** (one large-diff prompt can exceed it alone; the cascade then falls through) | response headers `x-ratelimit-limit-requests`, `x-ratelimit-limit-tokens`, 2026-10-02 | read the headers of any chat completion |
| Groq, `openai/gpt-oss-120b` | 30 requests/minute; 200,000 tokens/day | Groq rate-limits docs, 2026-10-01 (not in the headers) | Groq's rate-limits docs page |
| Gemini | per-model limits shown only in AI Studio for the project, not in public docs; requests/day reset at midnight Pacific | Gemini docs, 2026-10-01 | AI Studio → the project's rate limits |
| Mistral, `codestral-2508` | 125 requests/minute; 625,000 tokens/minute | response headers `x-ratelimit-limit-req-minute`, `x-ratelimit-limit-tokens-minute`, 2026-10-02 | read the headers of any chat completion |
| OpenRouter, `:free` models | about 50 requests/day | OpenRouter docs, 2026-10-01 | OpenRouter's limits docs page |
| OpenRouter key | `is_free_tier: true`, credit limit 0, usage 0 | `GET https://openrouter.ai/api/v1/key`, 2026-10-02 | same call |

## Volatile library versions
Installed versions, read with `importlib.metadata` on 2026-10-02 (pinned in `pyproject.toml` where installed):

| Library | Version | Note |
|---|---|---|
| LiteLLM | 1.103.1 | [[LiteLLM]] |
| Langfuse SDK | 4.15.6 | [[Langfuse]] |
| arq | 0.28.0 | [[arq]] |
| Alembic | 1.20.0 | [[Alembic]] |
| SQLAlchemy | 2.1.1 | [[SQLAlchemy]] |
| tree-sitter | not installed | [[tree-sitter]] |
| LangGraph | not installed | [[LangGraph]] |
| Qdrant client | not installed | [[Qdrant]] |
| Qdrant server | image `qdrant/qdrant:latest`, locally v1.19.1 (built 2026-09-03). **Unpinned**: `latest` moves | `docker image inspect qdrant/qdrant:latest` |

Re-verify with `.venv/bin/python -c "import importlib.metadata as m; print(m.version('<package>'))"` or `uv pip show --python .venv/bin/python <package>`. The venv has no `pip` (uv manages it).

## All pinned packages
Every package pinned in `pyproject.toml`, with the installed version read via `importlib.metadata` on 2026-10-02. Re-verify: `python -c "from importlib.metadata import version; print(version('<pkg>'))"`, or `scripts/check_vault.py` check 7 (pin named in the stack note).

| Package | Pinned | Installed (2026-10-02) | Match |
|---|---|---|---|
| `alembic` | 1.20.0 | 1.20.0 | ✅ |
| `arq` | 0.28.0 | 0.28.0 | ✅ |
| `fastapi` | 0.141.1 | 0.141.1 | ✅ |
| `httpx` | 0.28.1 | 0.28.1 | ✅ |
| `langfuse` | 4.15.6 | 4.15.6 | ✅ |
| `litellm` | 1.103.1 | 1.103.1 | ✅ |
| `psycopg` | 3.3.6 | 3.3.6 | ✅ |
| `pydantic` | 2.13.5 | 2.13.5 | ✅ |
| `pydantic-settings` | 2.15.0 | 2.15.0 | ✅ |
| `pyjwt` | 2.15.1 | 2.15.1 | ✅ |
| `redis` | 5.3.1 | 5.3.1 | ✅ |
| `sqlalchemy` | 2.1.1 | 2.1.1 | ✅ |
| `starlette` | 1.7.0 | 1.7.0 | ✅ |
| `uvicorn` | 0.54.0 | 0.54.0 | ✅ |
| `mypy` | 2.3.1 | 2.3.1 | ✅ |
| `pytest` | 9.1.1 | 9.1.1 | ✅ |
| `pytest-asyncio` | 1.4.0 | 1.4.0 | ✅ |
| `pytest-cov` | 7.1.0 | 7.1.0 | ✅ |
| `ruff` | 0.16.9 | 0.16.9 | ✅ |

## GitHub App
| Fact | Value | Last verified | How to re-verify |
|---|---|---|---|
| Permissions needed for the review path | Pull requests: Read & write; Contents: Read-only; Metadata: Read-only. Event: Pull request | 2026-10-02: `GET /app/installations` showed exactly these on installation `166565995`, and a real diff fetch of `Daksha1611/themis-test-repo` PR #2 succeeded | App JWT → `GET /app/installations`; then `fetch_pr_diff` on a test PR |
| Contents: Read-only is required | without it the diff request returns 403 "Resource not accessible by integration" | 2026-09-30 (live 403), fixed 2026-10-01 (Q50) | remove the permission on a test App and fetch a diff |

## Security taxonomy
| Fact | Value | Last verified | How to re-verify |
|---|---|---|---|
| CWE Top 25 edition pinned | 2024 (MITRE CWE view 1430, CWE 4.20) | 2026-10-01 ([[ADR-022 CWE Top 25 security taxonomy]]) | `https://cwe.mitre.org/data/definitions/1430.html` |
| Newest edition published | 2025 (view 1435). No 2026 edition: its archive page returned 404 | 2026-10-02 | `https://cwe.mitre.org/top25/` and `…/top25/archive/<year>/<year>_cwe_top25.html` |
