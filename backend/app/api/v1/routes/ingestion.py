from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.config import settings
from app.rag.document_processor import DocumentProcessor
from app.rag.chunker import RecursiveChunker
from app.rag.embeddings import DeterministicEmbeddingProvider
from app.rag.vector_store import QdrantVectorStore
from app.rag.ingestion import RAGIngestionService
from app.repositories.documents import DocumentRepository
from app.jobs.models import new_job
from app.jobs.service import enqueue

router = APIRouter()

@router.post("/{document_id}")
async def ingest_document(document_id: str, db: AsyncSession = Depends(get_db)):
    document = await DocumentRepository(db).get(document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found.")

    service = RAGIngestionService(
        processor=DocumentProcessor(),
        chunker=RecursiveChunker(),
        embeddings=DeterministicEmbeddingProvider(),
        vector_store=QdrantVectorStore(),
    )
    try:
        count = await service.ingest(document.storage_path, document.id, db)
        document.status = "indexed"
        await db.commit()
    except Exception as exc:
        document.status = "indexing_failed"
        await db.commit()
        raise HTTPException(status_code=422, detail=f"Document indexing failed: {exc}") from exc

    return {
        "document_id": document.id,
        "status": document.status,
        "chunks_indexed": count,
        "collection": settings.qdrant_collection,
    }


@router.post("/{document_id}/async")
async def enqueue_ingestion(document_id: str, db: AsyncSession = Depends(get_db)):
    document = await DocumentRepository(db).get(document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found.")

    async def worker(job):
        job.update(progress=15, message="Preparing document")
        service = RAGIngestionService(
            processor=DocumentProcessor(),
            chunker=RecursiveChunker(),
            embeddings=DeterministicEmbeddingProvider(),
            vector_store=QdrantVectorStore(),
        )
        job.update(progress=35, message="Extracting and chunking")
        count = await service.ingest(document.storage_path, document.id, db)
        document.status = "indexed"
        await db.commit()
        job.update(progress=90, message="Persisting retrieval index")
        return {"document_id": document.id, "chunks_indexed": count, "status": document.status}

    job = new_job("document_ingestion", document_id)
    enqueue(job, worker)
    return {"job_id": job.id, "status": job.status}
