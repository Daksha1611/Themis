"""Context builder (M4, ADR-027): chunker, sparse terms, embedding cache, hybrid index, retriever
and the eval's snapshot rules. A deterministic fake embedder and in-memory Qdrant: no model
download, no network, no running Qdrant service."""

import hashlib
from pathlib import Path

from qdrant_client import QdrantClient

from app.context.chunker import chunk_source
from app.context.embeddings import CachedEmbedder, EmbeddingCache
from app.context.index import HybridIndex
from app.context.retriever import hunks, retrieve
from app.context.sparse import sparse_vector, terms
from evals.context_eval import EXCLUDED, referenced

SOURCE = '''import os


def load_config(path):
    """Read the config file."""
    return open(path).read()


@cache
def parse_value(text):
    return int(text)


class ParamType:
    """A parameter type."""

    name = "text"

    def split_envvar_value(self, rv):
        return rv.split()

    @property
    def is_flag(self):
        return False
'''


class FakeEmbedder:
    """Bag-of-terms hashed into 16 dimensions: deterministic, and similar text scores higher."""

    name, dim = "fake", 16

    def __init__(self) -> None:
        self.calls = 0

    def encode(self, texts: list[str]) -> list[list[float]]:
        self.calls += len(texts)
        vectors = []
        for text in texts:
            v = [0.0] * self.dim
            for term in terms(text):
                v[int(hashlib.sha256(term.encode()).hexdigest(), 16) % self.dim] += 1.0
            norm = sum(x * x for x in v) ** 0.5 or 1.0
            vectors.append([x / norm for x in v])
        return vectors


def test_chunks_functions_class_header_and_methods_with_their_class() -> None:
    chunks = chunk_source("pkg/m.py", SOURCE)
    assert [(c.symbol, c.kind) for c in chunks] == [
        ("load_config", "function"),
        ("parse_value", "function"),
        ("ParamType", "class"),
        ("ParamType.split_envvar_value", "method"),
        ("ParamType.is_flag", "method"),
    ]
    decorated = chunks[1]
    assert decorated.code.startswith("@cache") and decorated.start_line == 9
    header = chunks[2]
    assert "split_envvar_value" not in header.code and 'name = "text"' in header.code
    assert chunks[4].code.lstrip().startswith("@property")


def test_sparse_terms_split_identifiers() -> None:
    assert {"split_envvar_value", "split", "envvar", "value"} <= set(terms("split_envvar_value"))
    assert {"paramtype", "param", "type"} <= set(terms("ParamType"))
    indices, values = sparse_vector("value value other")
    assert len(indices) == len(set(indices)) and sorted(values) == [1.0, 2.0]


def test_embedding_cache_embeds_each_text_once(tmp_path: Path) -> None:
    fake = FakeEmbedder()
    embedder = CachedEmbedder(fake, EmbeddingCache(tmp_path / "e.db"))
    first = embedder.encode(["a b", "c d"])
    again = CachedEmbedder(fake, EmbeddingCache(tmp_path / "e.db")).encode(["c d", "a b"])
    assert fake.calls == 2  # the second embedder read both from the cache
    assert [round(x, 5) for x in again[1]] == [round(x, 5) for x in first[0]]
    assert (embedder.hits, embedder.misses) == (0, 2)


def index_of(source: str = SOURCE) -> HybridIndex:
    index = HybridIndex(QdrantClient(":memory:"), "t", FakeEmbedder())
    index.add(
        chunk_source("pkg/m.py", source)
        + chunk_source("pkg/other.py", "def unrelated():\n    pass\n")
    )
    return index


def test_hybrid_search_ranks_the_matching_definition_first() -> None:
    results = index_of().search("rv = self.type.split_envvar_value(value)", limit=3)
    assert results[0][0].symbol == "ParamType.split_envvar_value"


DIFF = """diff --git a/pkg/caller.py b/pkg/caller.py
--- a/pkg/caller.py
+++ b/pkg/caller.py
@@ -10,3 +10,3 @@ def use(value):
     x = 1
-    rv = self.type.split_envvar_value(value)
+    rv = value
     return rv
"""


def test_retriever_respects_the_budget_and_skips_the_diffs_own_region() -> None:
    index = index_of()
    caller = "def use(value):\n" + "\n" * 8 + "    rv = self.type.split_envvar_value(value)\n"
    index.add(chunk_source("pkg/caller.py", caller))
    context = retrieve(index, DIFF, budget=40, count=lambda text: len(text.split()))
    assert context.token_budget_used <= 40
    symbols = [c.symbol for c in context.related_chunks]
    assert "use" not in symbols  # overlaps the changed lines of pkg/caller.py
    assert symbols[0] == "ParamType.split_envvar_value"
    assert all(c.reason.startswith("hybrid match to hunk 1") for c in context.related_chunks)
    assert hunks(DIFF)[0][:3] == ("pkg/caller.py", 10, 12)


def test_snapshot_excludes_tests_docs_changelogs_and_ci() -> None:
    for path in (
        "src/click/tests/test_x.py",
        "pkg/test_core.py",
        "pkg/conftest.py",
        "docs/conf.py",
        "CHANGES.rst",
        ".github/workflows/ci.py",
        "pkg/core_test.py",
    ):
        assert EXCLUDED.search(path), path
    for path in ("src/click/core.py", "rich/testing_utils.py", "fastapi/dependencies/utils.py"):
        assert not EXCLUDED.search(path), path


def test_referenced_names_come_from_changed_lines_only() -> None:
    files = {
        "pkg/caller.py": (
            "blob",
            "a = 1\n" * 10 + "    rv = self.type.split_envvar_value(value)\n" + "z = other()\n",
        )
    }
    diff = DIFF.replace("@@ -10,3 +10,3 @@", "@@ -10,2 +10,2 @@").replace("     x = 1\n", "")
    names = referenced(diff.replace("@@ -10,2 +10,2 @@", "@@ -11,1 +11,1 @@"), files)
    assert {"split_envvar_value", "value", "rv"} <= names and "other" not in names


def test_the_review_path_does_not_import_the_context_builder() -> None:
    """Context is not wired in (ADR-027): importing the worker and the review path must not
    load app.context. Checked in a fresh interpreter so other tests' imports cannot mask it."""
    import subprocess
    import sys

    code = (
        "import sys, app.worker.job, app.graph.baseline, app.llm; "
        "print(any(m.startswith('app.context') for m in sys.modules))"
    )
    out = subprocess.run(  # noqa: S603 (fixed argv: this interpreter and a constant)
        [sys.executable, "-c", code], capture_output=True, text=True, check=True
    )
    assert out.stdout.strip() == "False"
