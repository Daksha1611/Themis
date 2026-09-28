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
`[NOT YET BUILT]`

## 2. Job consumption
`[NOT YET BUILT]`

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
`[NOT YET BUILT]`

**Design reference** (see `vault/02 Architecture/GitHub Integration.md`):
- Owned by GitHub Integration (`app/github/`), which also owns GitHub App auth (JWT → installation token) and diff fetching.
- Posts the filtered findings as review comments, plus the guardrail notice when triggered.

## 8. Tracing and storage
`[NOT YET BUILT]`

## 9. Eval harness flow
`[NOT YET BUILT]`

## 10. Call graph index

| Caller | Function | Calls | File |
|--------|----------|-------|------|

No functions exist yet.
