"""Response cache for eval runs (M3 Step 4): SQLite at evals/.cache/responses.db (git-ignored).

The key is SHA-256 over (provider, model, full prompt messages, temperature, max_tokens), so any
change to the prompt, the model or the sampling settings is a miss. A hit never calls a provider.
Implements `app.llm.ResponseCache`; the review path uses it through `PinnedLLM` (ADR-024).
"""

import hashlib
import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path

from app.llm import LLMResponse

DEFAULT_PATH = Path("evals/.cache/responses.db")


class CacheMiss(Exception):
    """A miss in cache-only mode: the run must not call any provider."""


class ResponseCache:
    def __init__(self, path: Path = DEFAULT_PATH, cache_only: bool = False) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        self._db = sqlite3.connect(path)
        self._db.execute(
            "CREATE TABLE IF NOT EXISTS responses (key TEXT PRIMARY KEY, response TEXT NOT NULL, "
            "created_at TEXT NOT NULL, latency_ms INTEGER)"
        )
        self.cache_only = cache_only
        self.hits = 0
        self.misses = 0

    @staticmethod
    def key(
        provider: str,
        model: str,
        messages: list[dict[str, str]],
        temperature: float,
        max_tokens: int,
    ) -> str:
        payload = json.dumps(
            {
                "provider": provider,
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
            },
            sort_keys=True,
            ensure_ascii=False,
        )
        return hashlib.sha256(payload.encode()).hexdigest()

    def get(self, key: str) -> LLMResponse | None:
        row = self._db.execute("SELECT response FROM responses WHERE key = ?", (key,)).fetchone()
        if row is None:
            self.misses += 1
            if self.cache_only:
                raise CacheMiss(f"cache-only run: no cached response for key {key[:12]}")
            return None
        self.hits += 1
        return LLMResponse.model_validate_json(row[0])

    def put(self, key: str, response: LLMResponse) -> None:
        self._db.execute(
            "INSERT OR REPLACE INTO responses (key, response, created_at) VALUES (?, ?, ?)",
            (key, response.model_dump_json(), datetime.now(UTC).isoformat(timespec="seconds")),
        )
        self._db.commit()

    def contains(self, key: str) -> bool:
        """Whether a response is cached, without counting a hit or a miss."""
        row = self._db.execute("SELECT 1 FROM responses WHERE key = ?", (key,)).fetchone()
        return row is not None

    def set_latency(self, key: str, latency_ms: int) -> None:
        """The original call's latency, so reruns from the cache report the same latency."""
        self._db.execute("UPDATE responses SET latency_ms = ? WHERE key = ?", (latency_ms, key))
        self._db.commit()

    def latency(self, key: str) -> int | None:
        row = self._db.execute("SELECT latency_ms FROM responses WHERE key = ?", (key,)).fetchone()
        return None if row is None else row[0]

    @property
    def hit_rate(self) -> float | None:
        lookups = self.hits + self.misses
        return self.hits / lookups if lookups else None

    def close(self) -> None:
        self._db.close()
