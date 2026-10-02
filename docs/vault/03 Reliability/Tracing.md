---
name: Tracing
description: "Langfuse tracing: what each trace, span and generation records for webhooks and review jobs."
type: reliability
status: in-progress
tags: [reliability]
related:
  - "[[Review Graph]]"
  - "[[LLM Client]]"
  - "[[Langfuse]]"
  - "[[Operational Monitoring]]"
  - "[[ADR-006 Langfuse tracing]]"
  - "[[ADR-013 Langfuse cloud over self-hosting]]"
---

# Tracing

**Purpose:** see what every review did and what it cost.

- Tool: [[Langfuse]] (OpenTelemetry-compatible), cloud free tier ([[ADR-013 Langfuse cloud over self-hosting]])
- On from day one
- Logs tokens, cost, latency, and every [[Review Graph]] node's input/output
- Follows Langfuse's "What does a good trace look like?" guidance (installed Langfuse agent skill): nested observations, the LLM call as a `generation` with model, parameters, token usage and cost, meaningful root input/output, stable low-cardinality names, `environment` attribute

## What is traced (M2)
Helpers in `app/observability/tracing.py`: `observe()` (context manager; nests anything opened inside it), `trace_attributes()` (session, tags, metadata), `update()`.

**`webhook.received`** (one per `POST /webhook`): input `{event, action, repo, pr_number}`; output `{status_code, body}`.

**`review.job`** (one per review): session `<repo>#<pr>` (all reviews of one PR grouped), tag `baseline`, environment `development`. Input `{repo, pr_number, pr_title, head_sha}`; output the full `ReviewResult` ([[Finding Schema]]). Level `ERROR` with the error as status message when the review failed, `WARNING` when it was partial, so failed reviews can be filtered by level.

**Service name:** `OTEL_SERVICE_NAME` is set per container in `infra/docker-compose.yml` (`themis-api`, `themis-worker`), so spans don't report `unknown_service`.

| Child span | Captures |
|---|---|
| `github.auth` | installation ID in; `ok` out |
| `github.fetch_diff` | repo and PR in; `diff_chars`, `truncated` out |
| `baseline.review` | diff length in; `status`, `finding_count`, `parse_error_count`, `prompt_tokens`, `completion_tokens`, `cost_usd` out; `parse_errors` and the raw LLM response when parsing failed; `ERROR` level on failure |
| ↳ `llm.complete` (span) | cascade in; `provider` that answered, `model`, every attempt with its outcome out |
| ↳↳ `llm.generate` (generation, one per provider attempt) | full messages in; assistant message out (`content` plus the model's thinking as `reasoning_content`); `model`, `model_parameters`, `usage_details` (input, output), `cost_details` (list-price estimate); metadata `provider`, `reasoning_tokens`. Failed attempts are marked `ERROR` |
| `github.post_comments` | finding count in; `line_comments`, `summary_findings`, `rate_limited` out (or the no-issues / error comment) |
| `storage.write` | status in; `run_id` out |

Names keep the dotted `component.action` form: stable and free of dynamic values, as the best-practices page requires; not verb-first, a deliberate choice recorded in `docs/decision.md`.

Thinking is captured in the generation output because Langfuse truncates long metadata values (a first attempt stored only 200 of ~2,300 characters).

Secrets inside reviewed diffs are not masked before tracing (Q49).

**Code location:** `app/observability/tracing.py`.

Decision: [[ADR-006 Langfuse tracing]]. Langfuse is the only v1 source of latency, cost, and token metrics; a separate metrics stack ([[Operational Monitoring]]) is deferred to post-v1.
