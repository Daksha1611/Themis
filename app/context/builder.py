"""Production context builder (M4; ADR-014 as amended by ADR-030).

Per review: list the base commit's tree, pick the package the diff touches, fetch only the blob
sources not already cached, then chunk, embed (content-hash cache), index in an in-memory Qdrant
collection, and retrieve within the budget. Blob sources and embeddings are cached on disk by
content hash, so a PR re-processes only files changed since the cache last saw them. The base
commit is used because the retriever reads the diff's old-side line numbers.
"""

import asyncio
import re
import sqlite3
from functools import lru_cache
from pathlib import Path

from qdrant_client import QdrantClient

from app.context.chunker import Chunk, chunk_source
from app.context.embeddings import CachedEmbedder, EmbeddingCache, SentenceTransformerEmbedder
from app.context.index import HybridIndex
from app.context.retriever import retrieve
from app.context.structure import PackageIndex
from app.github.contents import fetch_blobs, fetch_tree
from app.schemas import ReviewContext

# Never indexed: tests, docs, changelogs, CI (the same rule as the eval snapshots, ADR-027).
EXCLUDED = re.compile(
    r"(^|/)(tests?|testing|docs?|\.github|\.circleci)/"
    r"|(^|/)(test_[^/]*|[^/]*_test|conftest)\.py$"
    r"|(^|/)(CHANGE|HISTORY|NEWS)",
    re.IGNORECASE,
)
MAX_FILES = 2000  # larger packages are not indexed (first review would fetch too many blobs)
DIFF_PATH = re.compile(r"^\+\+\+ b/(.+)$|^--- a/(.+)$", re.M)


class BlobCache:
    """SQLite cache of blob sources keyed by git blob SHA (content-addressed, never stale)."""

    def __init__(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        self._db = sqlite3.connect(path, check_same_thread=False)
        self._db.execute("CREATE TABLE IF NOT EXISTS blobs (sha TEXT PRIMARY KEY, source TEXT)")

    def get_many(self, shas: list[str]) -> dict[str, str]:
        found: dict[str, str] = {}
        for start in range(0, len(shas), 500):
            batch = shas[start : start + 500]
            rows = self._db.execute(
                f"SELECT sha, source FROM blobs WHERE sha IN ({','.join('?' * len(batch))})",  # noqa: S608
                batch,
            )
            found.update(dict(rows))
        return found

    def put_many(self, items: dict[str, str]) -> None:
        self._db.executemany("INSERT OR REPLACE INTO blobs VALUES (?, ?)", list(items.items()))
        self._db.commit()


def package_roots(paths: list[str]) -> list[str]:
    """Top-level packages: `pkg/` or `src/pkg/` directories holding an `__init__.py`."""
    roots = []
    for path in paths:
        parts = path.split("/")
        if parts[-1] != "__init__.py":
            continue
        if len(parts) == 2 or (len(parts) == 3 and parts[0] == "src"):
            roots.append("/".join(parts[:-1]) + "/")
    return sorted(roots)


def choose_root(paths: list[str], diff: str) -> str | None:
    """The package holding most of the diff's files; None if the diff touches no package."""
    touched = {a or b for b, a in DIFF_PATH.findall(diff)}
    counts = {root: sum(p.startswith(root) for p in touched) for root in package_roots(paths)}
    best = max(counts.items(), key=lambda kv: kv[1], default=(None, 0))
    return best[0] if best[1] else None


def package_files(tree: dict[str, str], root: str) -> dict[str, str]:
    return {
        path: sha
        for path, sha in tree.items()
        if path.startswith(root) and path.endswith(".py") and not EXCLUDED.search(path)
    }


@lru_cache
def _embedder(cache_dir: str) -> CachedEmbedder:
    # One model load per worker process.
    return CachedEmbedder(
        SentenceTransformerEmbedder(), EmbeddingCache(Path(cache_dir) / "embeddings.db")
    )


def build_from_sources(
    files: dict[str, str], root: str, diff: str, budget: int, embedder: CachedEmbedder
) -> ReviewContext:
    """Chunk, index and retrieve over a package snapshot (path -> source). CPU-bound."""
    chunks: list[Chunk] = [c for path, source in files.items() for c in chunk_source(path, source)]
    index = HybridIndex(QdrantClient(":memory:"), "review", embedder)
    index.add(chunks)
    return retrieve(index, diff, budget, structure=PackageIndex(files, root))


async def snapshot(
    token: str, repo_full_name: str, sha: str, diff: str, cache: BlobCache
) -> tuple[dict[str, str], str | None]:
    """The package source the diff touches at `sha`: (path -> source, package root)."""
    tree = await fetch_tree(token, repo_full_name, sha)
    root = choose_root(list(tree), diff)
    if root is None:
        return {}, None
    wanted = package_files(tree, root)
    if len(wanted) > MAX_FILES:
        return {}, None
    sources = cache.get_many(sorted(set(wanted.values())))
    missing = sorted(set(wanted.values()) - set(sources))
    if missing:
        fetched = await fetch_blobs(token, repo_full_name, missing)
        cache.put_many(fetched)
        sources.update(fetched)
    return {path: sources[sha] for path, sha in wanted.items()}, root


async def build_context(
    token: str, repo_full_name: str, base_sha: str, diff: str, budget: int, cache_dir: str
) -> ReviewContext:
    cache = BlobCache(Path(cache_dir) / "blobs.db")
    files, root = await snapshot(token, repo_full_name, base_sha, diff, cache)
    if not files or root is None:
        return ReviewContext(token_budget=budget)
    return await asyncio.to_thread(
        build_from_sources, files, root, diff, budget, _embedder(cache_dir)
    )
