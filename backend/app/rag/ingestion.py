from sqlalchemy.ext.asyncio import AsyncSession
from app.models.entities import DocumentChunk
from app.rag.chunker import RecursiveChunker
from app.rag.document_processor import DocumentProcessor
from app.rag.embeddings import EmbeddingProvider
from app.rag.vector_store import QdrantVectorStore

class RAGIngestionService:
    def __init__(
        self,
        processor: DocumentProcessor,
        chunker: RecursiveChunker,
        embeddings: EmbeddingProvider,
        vector_store: QdrantVectorStore,
    ):
        self.processor = processor
        self.chunker = chunker
        self.embeddings = embeddings
        self.vector_store = vector_store

    async def ingest(self, file_path: str, document_id: str, db: AsyncSession) -> int:
        pages = await self.processor.process(file_path, document_id)
        chunks = self.chunker.chunk(pages, document_id)
        if not chunks:
            raise ValueError("Document contains no extractable text.")

        vectors = await self.embeddings.embed([chunk.text for chunk in chunks])
        await self.vector_store.upsert(chunks, vectors)

        for chunk in chunks:
            db.add(DocumentChunk(
                id=chunk.chunk_id,
                document_id=chunk.document_id,
                chunk_index=chunk.chunk_index,
                text=chunk.text,
                page_number=chunk.page_number,
                metadata_json=chunk.metadata,
            ))
        await db.commit()
        return len(chunks)
