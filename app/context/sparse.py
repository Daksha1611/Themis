"""Sparse vectors for hybrid search (ADR-015, ADR-027): code-aware term counts.

Identifiers are kept whole and also split into their snake_case and camelCase parts, lowercased.
Each term maps to a stable 31-bit index (SHA-256 prefix); values are term counts. Qdrant's IDF
modifier on the sparse vector field supplies the inverse document frequency, so no BM25 index is
needed.
"""

import hashlib
import re
from collections import Counter

IDENTIFIER = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
CAMEL = re.compile(r"[A-Z]+(?=[A-Z][a-z])|[A-Z]?[a-z]+|[A-Z]+|[0-9]+")
MIN_LENGTH = 2


def terms(text: str) -> list[str]:
    out: list[str] = []
    for identifier in IDENTIFIER.findall(text):
        parts = [p for piece in identifier.split("_") for p in CAMEL.findall(piece)]
        for term in {identifier.lower(), *(p.lower() for p in parts)}:
            if len(term) >= MIN_LENGTH:
                out.append(term)
    return out


def term_index(term: str) -> int:
    return int.from_bytes(hashlib.sha256(term.encode()).digest()[:4], "big") & 0x7FFFFFFF


def sparse_vector(text: str) -> tuple[list[int], list[float]]:
    counts: Counter[int] = Counter(term_index(t) for t in terms(text))
    indices = sorted(counts)
    return indices, [float(counts[i]) for i in indices]
