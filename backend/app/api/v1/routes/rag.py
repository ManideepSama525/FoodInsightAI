from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from app.rag.pipeline import RAGPipeline

router = APIRouter()
pipeline = RAGPipeline()

class RetrievalRequest(BaseModel):
    query: str = Field(min_length=1, max_length=10000)
    document_ids: list[str] = []
    top_k: int = Field(default=8, ge=1, le=30)
    rerank_top_k: int = Field(default=5, ge=1, le=20)

@router.post("/retrieve")
async def retrieve(request: RetrievalRequest):
    try:
        context, citations, chunks = await pipeline.retrieve_context(
            request.query,
            request.document_ids,
            request.top_k,
            request.rerank_top_k,
        )
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Retrieval unavailable: {exc}") from exc

    return {
        "context": context,
        "citations": [c.__dict__ for c in citations],
        "retrieved_chunks": chunks,
    }
