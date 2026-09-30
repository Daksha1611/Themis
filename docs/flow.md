# Themis execution flow

The authoritative answer to "what does this system actually do when it runs?" It describes the running code, not the architecture diagram, and it is kept in sync with the code.

**Rules**
- Every function mentioned must exist in the codebase. Unbuilt sections are marked `[NOT YET BUILT]`.
- A new function gets its row in the call graph index in the same session it is added.
- A renamed or moved function is updated everywhere in this file in the same session.
- This file describes what the code does, not what it should do. If code and this file disagree, stop and flag it. Do not silently update either.

## How to read this document
- `→` calls
- `↳` returns
- `!` side effect (database write, queue write, external API call, log)

Each step lists: file and function, input, output, side effects, and error paths.

Sections that are not built may carry a **Design reference**: the approved design from the vault, with no function names. It is not a description of running code and is replaced by real steps when the code exists.

## 1. Webhook ingestion

Entry point: `POST /webhook` → `receive_webhook()` in `app/api/webhook.py`.

1. **Dependency** → `get_queue(request)` ↳ the `ArqRedis` pool stored on `app.state.arq_pool` by the lifespan in `app/main.py`.
2. `receive_webhook()` → `observe("webhook.received", input={"event": X-GitHub-Event})` ! Langfuse root observation (section 8).
3. → `_handle()`:
   1. Reads the raw body (`await request.body()`).
   2. → `get_settings().github_webhook_secret` → `verify_signature(body, X-Hub-Signature-256, secret)`: computes `"sha256=" + HMAC-SHA256(secret, body).hexdigest()` and compares with `hmac.compare_digest`.
      - Header missing, not prefixed `sha256=`, or mismatch ↳ **403** `{"error": "invalid signature"}` ! warning log.
   3. `X-GitHub-Event` ≠ `pull_request` ↳ **200** `{"ignored": true}`.
   4. `json.loads(body)`; invalid JSON ↳ **400** `{"error": "invalid JSON"}`.
   5. `action` not in `{"opened", "synchronize"}` ↳ **200** `{"ignored": true}`.
   6. `WebhookPayload.model_validate(data)` (`app/schemas.py`); missing fields ↳ **400** `{"error": "invalid payload"}` ! warning log.
   7. → `ReviewJob.from_payload(payload)` ↳ `ReviewJob(installation_id, repo_full_name, pr_number, head_sha, pr_title)`.
   8. → `update(trace, input={event, action, repo, pr_number})` ! Langfuse root input (becomes the trace input).
   9. → `queue.enqueue_job("handle_review_job", job.model_dump())` ! Redis write (arq queue `arq:queue`).
      - Any exception ↳ **500** `{"error": "could not enqueue job"}` ! error log with repo and PR number.
   10. ↳ **202** `{"queued": true, "pr": <pr_number>}`.
4. → `update(trace, output={"status_code", "body"})`; the observation ends when the `observe` block exits ! Langfuse.
5. Any unhandled exception inside `_handle()` is caught in `receive_webhook()` ! error log, observation marked `ERROR` ↳ **500** `{"error": "internal error"}`. No exception reaches GitHub.

Health: `GET /health` → `health()` in `app/api/health.py` ↳ `{"status": "ok"}`.

Container start: `alembic upgrade head` ! runs pending migrations under a Postgres advisory lock (`app/storage/migrations/env.py`), then uvicorn starts.

Startup (`lifespan()` in `app/main.py`): `logging.basicConfig` → `create_queue_client()` ! Redis connection → `init_tracing()`. Shutdown: close the arq pool → `close_client()` (shared GitHub httpx client) → `shutdown_tracing()` ! Langfuse flush.

## 2. Job consumption

Process: container start runs `alembic upgrade head` (advisory-locked), then `python -m arq app.worker.queue.WorkerSettings`. `WorkerSettings` (`app/worker/queue.py`) registers `functions = [handle_review_job]`, `max_tries = 5`, and `redis_settings` from `REDIS_URL`.

Worker startup: `startup(ctx)` → `logging.basicConfig` → `create_async_engine(DATABASE_URL)` → stores `ctx["engine"]` and `ctx["session_factory"]` → `init_tracing()`. Worker shutdown: `shutdown(ctx)` disposes the engine → `close_client()` → `shutdown_tracing()` ! Langfuse flush.

Per job: arq → `handle_review_job(ctx, job)` in `app/worker/job.py`:
1. `ReviewJob.model_validate(job)`; a `_Run` object collects what the job learns ! info log "Picked up review job".
2. → `trace_attributes(session_id="<repo>#<pr>", tags=["baseline"], metadata={repo, pr_number})` → `observe("review.job", input={repo, pr_number, pr_title, head_sha})` ! Langfuse root observation; every later span nests under it.
3. → `_review(ctx, run)`:
   1. Span `github.auth` → `get_installation_token(installation_id)` (section 7).
      - Failure (not rate limit) → `_store(ctx, run, "failed")` ↳ re-raised (no token, so no PR comment is possible).
   2. Span `github.fetch_diff` → `fetch_pr_diff(token, repo, pr_number)` (section 3) ↳ `PRDiff`; span output `{diff_chars, truncated}`.
      - Failure (not rate limit) → `_fail()`: posts the error comment, stores a `failed` run ↳ `"failed"`.
   3. Span `baseline.review` → `run_baseline_review(diff.text, {pr_title, repo_full_name})` (section 4) ↳ `BaselineResult`; span output `{status, finding_count, parse_error_count, prompt_tokens, completion_tokens, cost_usd}`, plus `parse_errors` and the raw LLM response when parsing failed. The `llm.complete` generation nests inside this span.
      - `status == "failed"` → `_fail()` ↳ `"failed"`.
   4. Span `github.post_comments`:
      - findings → `post_findings(token, repo, pr, head_sha, findings, diff.text)` (section 7); span output `{line_comments, summary_findings, rate_limited}`.
      - no findings → `post_review_comment(..., "⚖️ Themis found no logic bugs or security issues in this diff.")`.
      - any other exception → stores a `failed` run ↳ `"failed"` (no retry, so the LLM call is not repeated).
   5. → `_store(ctx, run, "success" | "partial")` (section 8) ↳ status.
4. `update(root, output=ReviewResult)`: the trace output is the full `ReviewResult` (findings, counts, llm_config, token_usage, cost_usd, latency_ms, status, error) ↳ status string stored by arq as the job result.

`_fail(ctx, run, token, error)`: span `github.post_comments` → `post_review_comment(..., "⚖️ Themis encountered an error during review. This run has been logged.")` (a failure here is logged, not raised) → `_store(ctx, run, "failed")`.

Error paths:
- `GitHubRetryableError` anywhere (rate limit) ! warning log, root output `{"status": "retrying"}` ↳ raises `arq.Retry(defer=retry_after)`.
- Any other escaping exception ! `logger.exception` with job metadata ↳ re-raised; arq records the failure.

## 3. Context building

**No repo context in M2: diff only.** The Context Builder (tree-sitter, Qdrant) is `[NOT YET BUILT]`.

Diff fetch: `fetch_pr_diff(token, repo_full_name, pr_number)` in `app/github/diff.py`:
1. → `gh.get_client()` → `GET https://api.github.com/repos/{repo}/pulls/{pr_number}` with `Accept: application/vnd.github.v3.diff` ! GitHub API call.
2. 404 ↳ raises `PRNotFoundError`; 410 ↳ raises `PRGoneError`; 403/429 with `Retry-After` ↳ `GitHubRetryableError`; other non-2xx ↳ `httpx.HTTPStatusError`.
3. Longer than `MAX_DIFF_CHARS` (100,000) ! warning log, text truncated (Q48).
4. ↳ `PRDiff(text, original_chars, truncated)`.

`commentable_lines(diff)` in the same file parses hunk headers and returns, per file, the new-side line numbers visible in the diff with their hunk index. Used by `build_review()` (section 7).

## 4. Review graph execution

**Single baseline pass. No LangGraph, no multi-pass yet** (M4).

`run_baseline_review(diff, pr_metadata)` in `app/graph/baseline.py`. **Never raises**: any exception ! `logger.exception` ↳ `BaselineResult(status="failed", parse_errors=["<Type>: <message>"])`.
1. Blank diff ↳ `BaselineResult(status="success", findings=[])` with no LLM call.
2. → `build_messages(diff, pr_metadata)`: system prompt with the diff between `<diff>` and `</diff>` and the statement that it is data, not instructions (inserted with `str.replace`, since diffs contain braces); user message `PR: {pr_title} in {repo_full_name}`.
3. → `complete(messages)` in `app/llm.py`:
   1. Opens `observe("llm.complete", as_type="generation", input=messages)` ! Langfuse generation, nested under `baseline.review`; records `model` and `model_parameters` (temperature, max_tokens).
   2. → `litellm.acompletion(model="openrouter/<LLM_MODEL>", messages, max_tokens, temperature, api_key=OPENROUTER_API_KEY)` ! OpenRouter API call. Any exception ↳ `LLMError(message, status_code)`.
   3. Cost: `_cost()` → `litellm.completion_cost()` from LiteLLM's bundled cost map (`LITELLM_LOCAL_MODEL_COST_MAP`); unavailable → 0.0 ! warning log.
   4. Generation updated with `output`, `usage_details {input, output}`, `cost_details {total}` ↳ `LLMResponse(content, model, prompt_tokens, completion_tokens, total_tokens, cost_usd)`.
4. → `parse_findings(content)`: `strip_fences()` → `json.loads`.
   - Not JSON, or not a JSON array ↳ no findings, one parse error containing the raw response, status `failed`.
   - Per element: drop any `confidence` key, validate as `Finding` with `confidence=0.0`; invalid elements → `parse_errors`.
5. Any parse errors ! warning log with the errors.
6. ↳ `BaselineResult(status, findings, llm_response, parse_errors)`: `success` (no errors), `partial` (some elements invalid), `failed` (unparseable).

## 5. Precision filter
`[NOT YET BUILT]`

## 6. Guardrails check
`[NOT YET BUILT]`

**Design reference** (see `vault/02 Architecture/Guardrails.md`):
- **Point 1, sanitize (between sections 3 and 4):** strip or neutralise instruction-like text in code comments, docstrings, and the PR description; wrap untrusted content in delimiters; the prompt states delimited content is data, never instructions.
- **Point 2, validate (between sections 4 and 5):** drop findings that reference the PR description, praise the code, or request approval.
- **On detection:** the review still runs on sanitized input; one comment noting suspicious content is posted (section 7); `guardrail_triggered` is set on the `ReviewResult`.

## 7. Comment posting

Owned by GitHub Integration (`app/github/`). All calls use one shared, connection-pooled `httpx.AsyncClient` from `gh.get_client()` (`app/github/client.py`), closed at shutdown by `close_client()`. `raise_if_rate_limited()` turns 403/429 + `Retry-After` into `GitHubRetryableError`.

**Installation token:** `get_installation_token(installation_id)` in `app/github/auth.py`:
1. Returns the cached token if it was fetched less than 50 minutes ago.
2. Otherwise → `get_jwt()`: RS256 JWT via PyJWT, payload `{iat: now-60, exp: now+600, iss: GITHUB_APP_ID}`.
3. → `POST /app/installations/{id}/access_tokens` with `github_headers(jwt)` ! GitHub API call → `raise_if_rate_limited()`; other non-2xx ↳ `httpx.HTTPStatusError`. 2xx: caches ↳ token.

**Findings:** `post_findings(token, repo, pr_number, head_sha, findings, diff)` in `app/github/comments.py`:
1. → `build_review(findings, diff)` → `commentable_lines(diff)`. A finding whose `line_end` is visible in the diff becomes a line comment (`side: RIGHT`; multi-line with `start_line` when `line_start` is in the same hunk). Every other finding is listed in the review body under "Findings outside the changed lines". Comment text comes from `format_finding()`: severity, category, message, 💡 suggestion. `raw_llm_confidence` is not shown (ADR-016).
2. → `_post_review()` → `POST /repos/{repo}/pulls/{pr}/reviews` `{commit_id: head_sha, event: "COMMENT", body, comments}` ! GitHub API call.
3. 422 with line comments ! warning log → re-posts the review with every finding in the body and no line comments.
4. ↳ `PostedReview(line_comments, summary_findings)`.

**PR-level comment:** `post_review_comment(token, repo, pr_number, body)` → `POST /repos/{repo}/issues/{pr}/comments` ! GitHub API call → `raise_if_rate_limited()` → `raise_for_status()`. Used for the no-issues and error messages.

## 8. Tracing and storage

**Tracing** (`app/observability/tracing.py`, Langfuse v4):
- `get_langfuse()` (cached) builds one `Langfuse` client with `environment=LANGFUSE_ENVIRONMENT`. Construction failure ! warning log ↳ `None`, and every helper becomes a no-op.
- `observe(name, as_type, input, metadata)`: a context manager that opens an observation as the current OpenTelemetry context (`start_as_current_observation`), so observations opened inside it, in any function, nest under it. On exception it marks the observation `ERROR` and re-raises; on exit it ends the observation. The trace name and input/output come from the root observation.
- `trace_attributes(session_id, tags, metadata)` wraps `propagate_attributes()` for trace-level attributes; entered before the root observation.
- `update(observation, **fields)` sets output, metadata, level, model, usage and cost.
- Every helper catches and logs its own errors. Spans are exported by the SDK's background exporter, so an unreachable Langfuse never blocks work.

Traces produced:
- `webhook.received` per `POST /webhook`: input `{event, action, repo, pr_number}`, output `{status_code, body}`.
- `review.job` per job, session `<repo>#<pr>`, tag `baseline`, input `{repo, pr_number, pr_title, head_sha}`, output the `ReviewResult`. Children: `github.auth` → `github.fetch_diff` → `baseline.review` (containing generation `llm.complete`) → `github.post_comments` → `storage.write`.

**Storage** (`app/storage/`):
- Schema is managed by Alembic (`app/storage/migrations/`): revision `75a08c2847ca` creates `review_runs` (M1 columns); `37e292134510` adds `finding_count`, `raw_finding_count`, `prompt_tokens`, `completion_tokens`, `model`, `diff_chars`, `diff_truncated`. `alembic upgrade head` runs when the api and worker containers start.
- `_store(ctx, run, status)` in `app/worker/job.py`: span `storage.write` → `create_run(session, run.row(status))` ! INSERT into `review_runs`, commit, refresh ↳ `ReviewRun`; span output `{run_id}`. **When:** once per job, last, after posting (or after the error comment on failure).
- `update_run(session, run_id, updates)` ! UPDATE; not called in M2.

## 9. Eval harness flow
`[NOT YET BUILT]`

## 10. Call graph index

| Caller | Function | Calls | File |
|--------|----------|-------|------|
| uvicorn (startup) | lifespan() | get_settings(), create_queue_client(), init_tracing(), close_client(), shutdown_tracing() | app/main.py |
| uvicorn | create_app() | FastAPI(), include_router() | app/main.py |
| FastAPI `GET /health` | health() | — | app/api/health.py |
| FastAPI `POST /webhook` | receive_webhook() | observe(), _handle(), update() | app/api/webhook.py |
| FastAPI dependency | get_queue() | — | app/api/webhook.py |
| receive_webhook() | _handle() | get_settings(), verify_signature(), WebhookPayload.model_validate(), ReviewJob.from_payload(), update(), ArqRedis.enqueue_job() | app/api/webhook.py |
| _handle() | verify_signature() | hmac.new(), hmac.compare_digest() | app/api/webhook.py |
| _handle() | ReviewJob.from_payload() | — | app/schemas.py |
| all modules | get_settings() | Settings() | app/config.py |
| lifespan() | create_queue_client() | redis_settings(), arq.create_pool() | app/worker/queue.py |
| arq worker (startup) | startup() | get_settings(), create_async_engine(), init_tracing() | app/worker/queue.py |
| arq worker (shutdown) | shutdown() | close_client(), shutdown_tracing() | app/worker/queue.py |
| arq worker | handle_review_job() | trace_attributes(), observe(), _review(), update() | app/worker/job.py |
| handle_review_job() | _review() | observe(), get_installation_token(), fetch_pr_diff(), run_baseline_review(), post_findings(), post_review_comment(), _fail(), _store(), update() | app/worker/job.py |
| _review() | _fail() | observe(), post_review_comment(), _store() | app/worker/job.py |
| _review(), _fail() | _store() | observe(), create_run(), _Run.row() | app/worker/job.py |
| handle_review_job() | _Run.result() | get_settings() | app/worker/job.py |
| _review() | get_installation_token() | get_jwt(), gh.get_client(), gh.github_headers(), gh.raise_if_rate_limited() | app/github/auth.py |
| get_installation_token() | get_jwt() | get_settings(), jwt.encode() | app/github/auth.py |
| auth, diff, comments | get_client() | httpx.AsyncClient() | app/github/client.py |
| lifespan(), shutdown() | close_client() | AsyncClient.aclose() | app/github/client.py |
| auth, diff, comments | raise_if_rate_limited() | — | app/github/client.py |
| _review() | fetch_pr_diff() | gh.get_client(), gh.github_headers(), gh.raise_if_rate_limited() | app/github/diff.py |
| build_review() | commentable_lines() | — | app/github/diff.py |
| _review() | post_findings() | build_review(), _post_review() | app/github/comments.py |
| post_findings() | build_review() | commentable_lines(), format_finding() | app/github/comments.py |
| post_findings() | _post_review() | gh.get_client(), gh.github_headers(), gh.raise_if_rate_limited() | app/github/comments.py |
| _review(), _fail() | post_review_comment() | gh.get_client(), gh.github_headers(), gh.raise_if_rate_limited() | app/github/comments.py |
| _review() | run_baseline_review() | build_messages(), complete(), parse_findings() | app/graph/baseline.py |
| parse_findings() | strip_fences() | — | app/graph/baseline.py |
| run_baseline_review() | complete() | get_settings(), observe(), litellm.acompletion(), _cost(), update() | app/llm.py |
| complete() | _cost() | litellm.completion_cost() | app/llm.py |
| _store() | create_run() | AsyncSession.add(), commit(), refresh() | app/storage/repository.py |
| — (not called in M2) | update_run() | AsyncSession.get(), commit(), refresh() | app/storage/repository.py |
| container start | alembic upgrade head | run_migrations_online() (advisory lock) | app/storage/migrations/env.py |
| webhook, worker, llm | observe() / update() / trace_attributes() | get_langfuse(), start_as_current_observation(), propagate_attributes() | app/observability/tracing.py |
