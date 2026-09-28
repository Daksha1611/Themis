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

## 1. Webhook ingestion
`[NOT YET BUILT]`

## 2. Job consumption
`[NOT YET BUILT]`

## 3. Context building
`[NOT YET BUILT]`

## 4. Review graph execution
`[NOT YET BUILT]`

## 5. Precision filter
`[NOT YET BUILT]`

## 6. Guardrails check
`[NOT YET BUILT]`

## 7. Comment posting
`[NOT YET BUILT]`

## 8. Tracing and storage
`[NOT YET BUILT]`

## 9. Eval harness flow
`[NOT YET BUILT]`

## 10. Call graph index

| Caller | Function | Calls | File |
|--------|----------|-------|------|

No functions exist yet.
