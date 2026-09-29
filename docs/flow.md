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
2. `receive_webhook()` → `start_trace("webhook.received", {"event": X-GitHub-Event})` ! Langfuse root observation (section 8).
3. → `_handle()`:
   1. Reads the raw body (`await request.body()`).
   2. → `get_settings().github_webhook_secret` → `verify_signature(body, X-Hub-Signature-256, secret)`: computes `"sha256=" + HMAC-SHA256(secret, body).hexdigest()` and compares with `hmac.compare_digest`.
      - Header missing, not prefixed `sha256=`, or mismatch ↳ **403** `{"error": "invalid signature"}` ! warning log.
   3. `X-GitHub-Event` ≠ `pull_request` ↳ **200** `{"ignored": true}`.
   4. `json.loads(body)`; invalid JSON ↳ **400** `{"error": "invalid JSON"}`.
   5. `action` not in `{"opened", "synchronize"}` ↳ **200** `{"ignored": true}`.
   6. `WebhookPayload.model_validate(data)` (`app/schemas.py`); missing fields ↳ **400** `{"error": "invalid payload"}` ! warning log.
   7. → `ReviewJob.from_payload(payload)` ↳ `ReviewJob(installation_id, repo_full_name, pr_number, head_sha, pr_title)`.
   8. → `update_trace(trace, {event, action, repo, pr_number})` ! Langfuse metadata.
   9. → `queue.enqueue_job("handle_review_job", job.model_dump())` ! Redis write (arq queue `arq:queue`).
      - Any exception ↳ **500** `{"error": "could not enqueue job"}` ! error log with repo and PR number.
   10. ↳ **202** `{"queued": true, "pr": <pr_number>}`.
4. → `end_trace(trace, {"status_code": ...})` ! Langfuse.
5. Any unhandled exception inside `_handle()` is caught in `receive_webhook()` ! error log, `end_trace(..., error=exc)` ↳ **500** `{"error": "internal error"}`. No exception reaches GitHub.

Health: `GET /health` → `health()` in `app/api/health.py` ↳ `{"status": "ok"}`.

Startup (`lifespan()` in `app/main.py`): `logging.basicConfig` → `create_async_engine(DATABASE_URL)` → `ensure_schema(engine)` ! `CREATE TABLE IF NOT EXISTS review_runs` → `create_queue_client()` ! Redis connection → `init_tracing()`. Shutdown: close the arq pool, dispose the engine, `shutdown_tracing()` ! Langfuse flush.

## 2. Job consumption

Process: `python -m arq app.worker.queue.WorkerSettings`. `WorkerSettings` (`app/worker/queue.py`) registers `functions = [handle_review_job]`, `max_tries = 5`, and `redis_settings` from `REDIS_URL`.

Worker startup: `startup(ctx)` → `logging.basicConfig` → `create_async_engine(DATABASE_URL)` → `ensure_schema(engine)` ! `CREATE TABLE IF NOT EXISTS review_runs` (a concurrent-create `IntegrityError` is logged and ignored) → stores `ctx["engine"]` and `ctx["session_factory"]` → `init_tracing()`. Worker shutdown: `shutdown(ctx)` disposes the engine and calls `shutdown_tracing()`.

Per job: arq → `handle_review_job(ctx, job)` in `app/worker/job.py`:
1. `ReviewJob.model_validate(job)` ! info log "Picked up review job".
2. → `start_trace("review.job", {repo, pr_number, head_sha, installation_id})` ! Langfuse.
3. Span `github.installation_token` → `get_installation_token(installation_id)` (section 7).
4. Span `github.post_comment` → `post_review_comment(token, repo, pr_number, "⚖️ Themis is reviewing this PR.")` (section 7) ! info log.
5. Span `storage.create_run` → `create_run(session, {...status: "dummy"...})` (section 8).
6. → `end_trace(trace, {"status": "dummy_complete", "run_id": ...})` ↳ `"dummy_complete"` (stored by arq as the job result).

Error paths:
- `GitHubRetryableError` (rate limit) ! warning log, span and trace ended with error ↳ raises `arq.Retry(defer=retry_after)`; arq re-queues until `max_tries`.
- Any other exception ! `logger.exception` with the job metadata, span and trace ended with error ↳ re-raised; arq records the failure.

## 3. Context building
`[NOT YET BUILT]`

**Design reference** (see `vault/02 Architecture/Context Builder.md`, ADR-014, ADR-015):
- The PR diff comes from GitHub Integration (`app/github/`).
- Indexing: full index of the default branch on install; per PR, incremental re-index of changed files plus their direct importers only; a manual re-index command.
- Retrieval: local sentence-transformers embeddings plus Qdrant native sparse vectors, fused with Reciprocal Rank Fusion.
- Output: a `ReviewContext`, which goes to the guardrail sanitize step (section 6) before the review graph.

## 4. Review graph execution
`[NOT YET BUILT]`

## 5. Precision filter
`[NOT YET BUILT]`

## 6. Guardrails check
`[NOT YET BUILT]`

**Design reference** (see `vault/02 Architecture/Guardrails.md`):
- **Point 1, sanitize (between sections 3 and 4):** strip or neutralise instruction-like text in code comments, docstrings, and the PR description; wrap untrusted content in delimiters; the prompt states delimited content is data, never instructions.
- **Point 2, validate (between sections 4 and 5):** drop findings that reference the PR description, praise the code, or request approval.
- **On detection:** the review still runs on sanitized input; one comment noting suspicious content is posted (section 7); `guardrail_triggered` is set on the `ReviewResult`.

## 7. Comment posting

Owned by GitHub Integration (`app/github/`).

**Installation token:** `get_installation_token(installation_id)` in `app/github/auth.py`:
1. Returns the cached token if it was fetched less than 50 minutes ago (in-process dict keyed by installation ID).
2. Otherwise → `get_jwt()`: RS256 JWT via PyJWT, payload `{iat: now-60, exp: now+600, iss: GITHUB_APP_ID}`, signed with `GITHUB_PRIVATE_KEY`.
3. → `http_client()` → `POST https://api.github.com/app/installations/{id}/access_tokens` with `github_headers(jwt)` ! GitHub API call.
4. Non-2xx ↳ `httpx.HTTPStatusError` (propagates to the job). 2xx: caches and ↳ the token.

**Comment:** `post_review_comment(token, repo_full_name, pr_number, body)` in `app/github/comments.py`:
1. → `http_client()` → `POST https://api.github.com/repos/{repo}/issues/{pr_number}/comments` with `github_headers(token)` and `{"body": body}` ! GitHub API call.
2. 403 or 429 **with** a `Retry-After` header ! warning log ↳ raises `GitHubRetryableError(retry_after)`.
3. Any other non-2xx ↳ `httpx.HTTPStatusError`. 2xx ↳ `None`.

M1 posts only this PR-level comment: no line-level review comments, no guardrail notice.

## 8. Tracing and storage

**Tracing** (`app/observability/tracing.py`, Langfuse v4):
- `get_langfuse()` (cached) builds one `Langfuse` client from config. Construction failure ! warning log ↳ `None`, and every helper becomes a no-op.
- `start_trace(name, metadata)` → `client.start_observation(...)`: a root observation, which creates the trace.
- `update_trace()`, `start_span()` (child observation), and `end_span()` / `end_trace()` (`update(output, level="ERROR", status_message)` on error, then `end()`).
- Spans are exported by the SDK's background OpenTelemetry exporter, so an unreachable Langfuse never blocks a request. Every helper catches and logs its own errors.
- **When:** `webhook.received` wraps each `POST /webhook` (section 1). `review.job` wraps each job, with child spans `github.installation_token`, `github.post_comment`, `storage.create_run` (section 2).

**Storage** (`app/storage/`):
- `ensure_schema(engine)` in `repository.py` runs `CREATE TABLE IF NOT EXISTS review_runs` ! DB DDL, at API startup and at worker startup. Temporary until Alembic (Open Question Q44).
- `create_run(session, run_data)` ! INSERT into `review_runs`, commit, refresh ↳ `ReviewRun`. **When:** step 5 of the job, after the comment is posted and before the trace ends.
- `update_run(session, run_id, updates)` ! UPDATE, commit ↳ `ReviewRun`; raises `LookupError` if the row is missing. Not called anywhere in M1.

## 9. Eval harness flow
`[NOT YET BUILT]`

## 10. Call graph index

| Caller | Function | Calls | File |
|--------|----------|-------|------|
| uvicorn (startup) | lifespan() | get_settings(), ensure_schema(), create_queue_client(), init_tracing(), shutdown_tracing() | app/main.py |
| uvicorn | create_app() | FastAPI(), include_router() | app/main.py |
| FastAPI `GET /health` | health() | — | app/api/health.py |
| FastAPI `POST /webhook` | receive_webhook() | start_trace(), _handle(), end_trace() | app/api/webhook.py |
| FastAPI dependency | get_queue() | — | app/api/webhook.py |
| receive_webhook() | _handle() | get_settings(), verify_signature(), WebhookPayload.model_validate(), ReviewJob.from_payload(), update_trace(), ArqRedis.enqueue_job() | app/api/webhook.py |
| _handle() | verify_signature() | hmac.new(), hmac.compare_digest() | app/api/webhook.py |
| _handle() | ReviewJob.from_payload() | — | app/schemas.py |
| all modules | get_settings() | Settings() | app/config.py |
| lifespan() | create_queue_client() | redis_settings(), arq.create_pool() | app/worker/queue.py |
| arq worker (startup) | startup() | get_settings(), ensure_schema(), init_tracing() | app/worker/queue.py |
| arq worker (shutdown) | shutdown() | shutdown_tracing() | app/worker/queue.py |
| arq worker | handle_review_job() | start_trace(), start_span(), get_installation_token(), post_review_comment(), create_run(), end_span(), end_trace() | app/worker/job.py |
| handle_review_job() | get_installation_token() | get_jwt(), http_client(), github_headers() | app/github/auth.py |
| get_installation_token() | get_jwt() | get_settings(), jwt.encode() | app/github/auth.py |
| handle_review_job() | post_review_comment() | http_client(), github_headers() | app/github/comments.py |
| lifespan(), startup() | ensure_schema() | AsyncEngine.begin() | app/storage/repository.py |
| handle_review_job() | create_run() | AsyncSession.add(), commit(), refresh() | app/storage/repository.py |
| — (not called in M1) | update_run() | AsyncSession.get(), commit(), refresh() | app/storage/repository.py |
| webhook, worker | start_trace() / update_trace() / end_trace() | get_langfuse(), Langfuse.start_observation() | app/observability/tracing.py |
| handle_review_job() | start_span() / end_span() | observation.start_observation(), update(), end() | app/observability/tracing.py |
