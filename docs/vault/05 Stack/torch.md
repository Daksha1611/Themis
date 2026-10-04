---
name: torch
description: "PyTorch, CPU-only build: the runtime under sentence-transformers for local embeddings."
type: tech
status: in-progress
tags: [tech]
related:
  - "[[sentence-transformers]]"
  - "[[Context Builder]]"
version: 2.14.1 (CPU build `2.14.1+cpu`; pinned in the context extra; read via importlib.metadata 2026-10-04)
---

# torch

The runtime under [[sentence-transformers]] (`all-MiniLM-L6-v2`, [[ADR-015 Local embeddings and Qdrant native hybrid search]]).

**CPU-only** to keep installs and the Docker image small. It is installed from the PyTorch CPU index before the project's `context` extra:

`pip install torch==2.14.1 --index-url https://download.pytorch.org/whl/cpu`

CI does the same. Measured on this machine: about 34 chunks per second with MiniLM on CPU.
