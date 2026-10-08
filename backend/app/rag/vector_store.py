from typing import Any
from qdrant_client import AsyncQdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

from app.core.config import settings
from app.rag.models import RetrievedChunk, TextChunk

class QdrantVectorStore:
    def __init__(self, client: AsyncQdrantClient | None = None):
        self.client = client or AsyncQdrantClient(url=settings.qdrant_url)
        self.collection = settings.qdrant_collection

    async def ensure_collection(self, dimension: int) -> None:
        collections = await self.client.get_collections()
        names = {item.name for item in collections.collections}
        if self.collection not in names:
            await self.client.create_collection(
                collection_name=self.collection,
                vectors_config=VectorParams(size=dimension, distance=Distance.COSINE),
            )

    async def upsert(self, chunks: list[TextChunk], vectors: list[list[float]]) -> None:
        await self.ensure_collection(len(vectors[0]) if vectors else 384)
        points = [
            PointStruct(
                id=chunk.chunk_id,
                vector=vector,
                payload={
                    "document_id": chunk.document_id,
                    "chunk_id": chunk.chunk_id,
                    "chunk_index": chunk.chunk_index,
                    "text": chunk.text,
                    "page_number": chunk.page_number,
                    **chunk.metadata,
                },
            )
            for chunk, vector in zip(chunks, vectors, strict=True)
        ]
        if points:
            await self.client.upsert(collection_name=self.collection, points=points)

    async def search(
        self,
        vector: list[float],
        limit: int,
        document_ids: list[str] | None = None,
    ) -> list[RetrievedChunk]:
        from qdrant_client.models import Filter, FieldCondition, MatchAny

        query_filter = None
        if document_ids:
            query_filter = Filter(
                must=[FieldCondition(key="document_id", match=MatchAny(any=document_ids))]
            )

        result = await self.client.query_points(
            collection_name=self.collection,
            query=vector,
            query_filter=query_filter,
            limit=limit,
            with_payload=True,
        )
        output = []
        for point in result.points:
            payload: dict[str, Any] = point.payload or {}
            chunk = TextChunk(
                chunk_id=str(payload["chunk_id"]),
                document_id=str(payload["document_id"]),
                chunk_index=int(payload.get("chunk_index", 0)),
                text=str(payload.get("text", "")),
                page_number=payload.get("page_number"),
                metadata={k: v for k, v in payload.items() if k not in {
                    "chunk_id", "document_id", "chunk_index", "text", "page_number"
                }},
            )
            output.append(RetrievedChunk(chunk=chunk, score=float(point.score), metadata=payload))
        return output
