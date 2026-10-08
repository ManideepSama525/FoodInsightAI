from pydantic import BaseModel, Field
from typing import Any

class Source(BaseModel):
    title: str
    source: str
    page: int | None = None
    document_id: str | None = None
    chunk_id: str | None = None

class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=10000)
    document_ids: list[str] = []
    image_id: str | None = None
    mode: str = "assistant"

class ChatResponse(BaseModel):
    answer: str
    sources: list[Source]
    retrieved_chunks: list[dict[str, Any]] = []
    confidence: float | None = None
    warnings: list[str] = []
    processing_time_ms: int
    model: str | None = None
    vision: dict[str, Any] | None = None
