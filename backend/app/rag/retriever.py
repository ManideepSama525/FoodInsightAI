from app.core.config import settings
from app.rag.embeddings import EmbeddingProvider
from app.rag.models import RetrievedChunk
from app.rag.vector_store import QdrantVectorStore

class Retriever:
    def __init__(self, embeddings: EmbeddingProvider, vector_store: QdrantVectorStore):
        self.embeddings = embeddings
        self.vector_store = vector_store

    async def retrieve(
        self,
        query: str,
        document_ids: list[str] | None = None,
        top_k: int | None = None,
    ) -> list[RetrievedChunk]:
        vectors = await self.embeddings.embed([query])
        return await self.vector_store.search(
            vectors[0],
            limit=top_k or settings.top_k,
            document_ids=document_ids,
        )
