# Themis

> An AI code reviewer that weighs the evidence before it speaks.

Themis is a GitHub App that automatically reviews pull requests, paired with a reliability layer that measures review quality and blocks changes that make it worse. The core promise is trustworthy judgment: high precision, low noise, and every design decision backed by benchmark numbers.

**Status:** planning. No application code yet.

## v1 scope
- Python repositories only
- Findings limited to logic bugs and security issues
- No style or formatting comments

## Training data rule
The precision filter is trained **only on findings generated from dev-split benchmark cases, never holdout**. `training/build_training_set.py` enforces this by rejecting any case ID present in the holdout split. Holdout numbers are only meaningful if the holdout never touches training.

## Documentation
- [`docs/vault/`](docs/vault/): the project knowledge vault (Obsidian). Start at [`00 Index.md`](docs/vault/00%20Index.md).
- [`docs/flow.md`](docs/flow.md): what the code actually does at runtime.
- [`docs/decision.md`](docs/decision.md): why each change was made.
