"""Hybrid chunk index in Qdrant (ADR-015): dense vectors plus sparse term vectors with Qdrant's
IDF modifier, fused with Reciprocal Rank Fusion. Tests and the eval use qdrant-client's
in-memory mode."""

import uuid
from dataclasses import asdict

from qdrant_client import QdrantClient, models

from app.context.chunker import Chunk
from app.context.embeddings import Embedder
from app.context.sparse import sparse_vector


class HybridIndex:
    def __init__(self, client: QdrantClient, collection: str, embedder: Embedder) -> None:
        self.client, self.collection, self.embedder = client, collection, embedder
        client.create_collection(
            collection,
            vectors_config={
                "dense": models.VectorParams(size=embedder.dim, distance=models.Distance.COSINE)
            },
            sparse_vectors_config={
                "sparse": models.SparseVectorParams(modifier=models.Modifier.IDF)
            },
        )

    def add(self, chunks: list[Chunk]) -> None:
        if not chunks:
            return
        dense = self.embedder.encode([c.code for c in chunks])
        points = []
        for chunk, vector in zip(chunks, dense, strict=True):
            indices, values = sparse_vector(chunk.code)
            points.append(
                models.PointStruct(
                    id=str(uuid.uuid4()),
                    vector={
                        "dense": vector,
                        "sparse": models.SparseVector(indices=indices, values=values),
                    },
                    payload=asdict(chunk),
                )
            )
        self.client.upsert(self.collection, points)

    def search(self, query: str, limit: int = 20) -> list[tuple[Chunk, float]]:
        dense = self.embedder.encode([query])[0]
        indices, values = sparse_vector(query)
        prefetch = [models.Prefetch(query=dense, using="dense", limit=limit * 2)]
        if indices:
            sparse = models.SparseVector(indices=indices, values=values)
            prefetch.append(models.Prefetch(query=sparse, using="sparse", limit=limit * 2))
        result = self.client.query_points(
            self.collection,
            prefetch=prefetch,
            query=models.FusionQuery(fusion=models.Fusion.RRF),
            limit=limit,
            with_payload=True,
        )
        return [(Chunk(**p.payload), p.score) for p in result.points if p.payload]
