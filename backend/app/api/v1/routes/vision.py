from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.repositories.documents import DocumentRepository
from app.vision.service import VisionService

router = APIRouter()

@router.post("/{document_id}")
async def analyze_image(document_id: str, db: AsyncSession = Depends(get_db)):
    document = await DocumentRepository(db).get(document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Image document not found.")
    if document.document_type != "image":
        raise HTTPException(status_code=400, detail="Document is not an image.")

    try:
        result = await VisionService().analyze(document.storage_path)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"Image analysis failed: {exc}") from exc

    return {
        "document_id": document.id,
        "filename": document.filename,
        "result": result.model_dump(),
    }
