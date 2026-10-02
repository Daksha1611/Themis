---
name: PyJWT
description: "PyJWT: signs the GitHub App JWT (RS256)."
type: tech
status: done
tags: [tech]
related:
  - "[[GitHub Integration]]"
  - "[[ADR-020 M1 runtime dependencies]]"
version: 2.15.1
---

# PyJWT

**What it is:** JSON Web Token library for Python. Installed with the `crypto` extra (cryptography 50.0.1) for RS256.

**What it does in Themis:** Signs the GitHub App JWT used to request installation tokens.

**Used by:** [[GitHub Integration]], [[ADR-020 M1 runtime dependencies]]

**Version:** 2.15.1 (installed 2026-09-29).
