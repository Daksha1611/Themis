"""Dense embeddings (ADR-015): a local sentence-transformers model, CPU only, behind a
content-hash cache (ADR-027). The model is loaded lazily, on first use."""

import hashlib
import sqlite3
from array import array
from functools import cached_property
from pathlib import Path
from typing import Any, Protocol

MODEL = "sentence-transformers/all-MiniLM-L6-v2"


class Embedder(Protocol):
    name: str
    dim: int

    def encode(self, texts: list[str]) -> list[list[float]]: ...


class SentenceTransformerEmbedder:
    """all-MiniLM-L6-v2 on CPU: 384 dimensions, normalised. Inputs past 256 tokens are
    truncated by the model; the sparse vector still covers the whole chunk."""

    dim = 384

    def __init__(self, name: str = MODEL) -> None:
        self.name = name

    @cached_property
    def _model(self) -> Any:
        from sentence_transformers import SentenceTransformer  # noqa: PLC0415 (heavy import)

        return SentenceTransformer(self.name, device="cpu")

    def encode(self, texts: list[str]) -> list[list[float]]:
        vectors = self._model.encode(texts, batch_size=64, normalize_embeddings=True)
        return [list(map(float, v)) for v in vectors]


class EmbeddingCache:
    """SQLite cache keyed by SHA-256 of (model name, text); vectors stored as float32."""

    def __init__(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        self._db = sqlite3.connect(path)
        self._db.execute("CREATE TABLE IF NOT EXISTS vectors (key TEXT PRIMARY KEY, v BLOB)")

    @staticmethod
    def key(model: str, text: str) -> str:
        return hashlib.sha256(f"{model}\0{text}".encode()).hexdigest()

    def get_many(self, keys: list[str]) -> dict[str, list[float]]:
        found: dict[str, list[float]] = {}
        for start in range(0, len(keys), 500):
            batch = keys[start : start + 500]
            rows = self._db.execute(
                f"SELECT key, v FROM vectors WHERE key IN ({','.join('?' * len(batch))})",  # noqa: S608
                batch,
            )
            found.update({k: array("f", v).tolist() for k, v in rows})
        return found

    def put_many(self, items: dict[str, list[float]]) -> None:
        self._db.executemany(
            "INSERT OR REPLACE INTO vectors VALUES (?, ?)",
            [(k, array("f", v).tobytes()) for k, v in items.items()],
        )
        self._db.commit()


class CachedEmbedder:
    """Embeds only texts not already cached; counts hits and misses."""

    def __init__(self, embedder: Embedder, cache: EmbeddingCache) -> None:
        self.embedder, self.cache = embedder, cache
        self.name, self.dim = embedder.name, embedder.dim
        self.hits = self.misses = 0

    def encode(self, texts: list[str]) -> list[list[float]]:
        keys = [EmbeddingCache.key(self.name, t) for t in texts]
        found = self.cache.get_many(list(dict.fromkeys(keys)))
        todo = {k: t for k, t in zip(keys, texts, strict=True) if k not in found}
        self.hits += sum(k in found for k in keys)
        self.misses += len(keys) - sum(k in found for k in keys)
        if todo:
            fresh = dict(zip(todo, self.embedder.encode(list(todo.values())), strict=True))
            self.cache.put_many(fresh)
            found.update(fresh)
        return [found[k] for k in keys]
