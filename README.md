# Themis

> An AI code reviewer that weighs the evidence before it speaks.

Themis is a GitHub App that automatically reviews pull requests, paired with a reliability layer that measures review quality and blocks changes that make it worse. The core promise is trustworthy judgment: high precision, low noise, and every design decision backed by benchmark numbers.

**Status:** M1 (skeleton) and M2 (baseline reviewer) are built and verified on a live GitHub PR. M3 (benchmark and eval harness) is in progress. There are no benchmark numbers yet.

## v1 scope
- Python repositories only
- Findings limited to logic bugs and security issues
- No style or formatting comments

## Limitations
- **Public repositories only.** Themis sends PR diffs, unmasked, to free-tier LLM providers and to Langfuse cloud for tracing. Some providers' free-tier terms permit using submitted data to improve their products (Google's Gemini API free tier states this). Do not install Themis on private repositories.
- Secret masking is required before any private-repo support, and is not part of v1.

## Training data rule
The precision filter is trained **only on findings generated from dev-split benchmark cases, never holdout**. `training/build_training_set.py` (planned, with the precision filter) will enforce this by rejecting any case ID present in the holdout split. Holdout numbers are only meaningful if the holdout never touches training.

## Documentation
- [`docs/vault/`](docs/vault/): the project knowledge vault (Obsidian). Start at [`00 Index.md`](docs/vault/00%20Index.md).
- [`docs/flow.md`](docs/flow.md): what the code actually does at runtime.
- [`docs/decision.md`](docs/decision.md): why each change was made.
- [`scripts/check_vault.py`](scripts/check_vault.py): run in CI; fails the build when the vault, `docs/flow.md` and the code drift apart.
