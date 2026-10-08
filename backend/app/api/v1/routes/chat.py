from pathlib import Path
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.chat import ChatRequest, ChatResponse
from app.chat.service import ChatService
from app.core.database import get_db
from app.repositories.documents import DocumentRepository

router = APIRouter()

@router.post("", response_model=ChatResponse)
async def chat(request: ChatRequest, db: AsyncSession = Depends(get_db)) -> ChatResponse:
    image_path = None

    if request.image_id:
        image_document = await DocumentRepository(db).get(request.image_id)
        if not image_document:
            raise HTTPException(status_code=404, detail="Image document not found.")
        if image_document.document_type != "image":
            raise HTTPException(status_code=400, detail="image_id must refer to an image.")
        image_path = image_document.storage_path

    try:
        result = await ChatService().answer(
            request.message,
            request.document_ids,
            image_path,
        )
        return ChatResponse(**result)
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail=f"Grounded multimodal chat service unavailable: {exc}",
        ) from exc
