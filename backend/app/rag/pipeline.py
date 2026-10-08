from app.rag.context import ContextBuilder, CitationRecord
from app.rag.embeddings import DeterministicEmbeddingProvider
from app.rag.reranker import LexicalReranker
from app.rag.retriever import Retriever
from app.rag.vector_store import QdrantVectorStore

class RAGPipeline:
    def __init__(self):
        embeddings = DeterministicEmbeddingProvider()
        store = QdrantVectorStore()
        self.retriever = Retriever(embeddings, store)
        self.reranker = LexicalReranker()
        self.context_builder = ContextBuilder()

    async def retrieve_context(
        self,
        query: str,
        document_ids: list[str] | None = None,
        top_k: int = 8,
        rerank_top_k: int = 5,
    ) -> tuple[str, list[CitationRecord], list[dict]]:
        retrieved = await self.retriever.retrieve(query, document_ids, top_k)
        reranked = self.reranker.rerank(query, retrieved, rerank_top_k)
        context, citations = self.context_builder.build(reranked)
        chunks = [
            {
                "chunk_id": item.chunk.chunk_id,
                "document_id": item.chunk.document_id,
                "page": item.chunk.page_number,
                "score": item.score,
                "text": item.chunk.text,
            }
            for item in reranked
        ]
        return context, citations, chunks
