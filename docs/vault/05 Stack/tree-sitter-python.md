---
name: tree-sitter-python
description: "tree-sitter-python: the Python grammar for tree-sitter, used by the context builder's chunker."
type: tech
status: in-progress
tags: [tech]
related:
  - "[[tree-sitter]]"
  - "[[Context Builder]]"
version: 0.25.0 (pinned in the context extra; read via importlib.metadata 2026-10-04)
---

# tree-sitter-python

The Python grammar for [[tree-sitter]]. Used by `app/context/chunker.py` (M4, [[ADR-027 Eval-time repo context]]).

**API checked against the installed versions (tree-sitter 0.26.0, tree-sitter-python 0.25.0):** language loading changed in recent releases. It is now `Language(tree_sitter_python.language())` and `Parser(language)`; there are no compiled `.so` grammars and no `set_language()`.
