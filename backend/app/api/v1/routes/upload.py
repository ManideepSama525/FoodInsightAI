from pathlib import Path
from time import perf_counter
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.security import validate_upload_metadata, sniff_content_type
from app.models.entities import Document
from app.repositories.documents import DocumentRepository
from app.services.file_storage import LocalFileStorage
from app.schemas.documents import DocumentOut

router = APIRouter()

@router.post("", response_model=DocumentOut)
async def upload(file: UploadFile = File(...), db: AsyncSession = Depends(get_db)):
    started = perf_counter()
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename is required.")

    content = await file.read()
    try:
        validate_upload_metadata(
            file.filename, file.content_type, len(content), settings.max_upload_mb
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    mime = file.content_type or sniff_content_type(file.filename)
    suffix = Path(file.filename).suffix.lower()
    document_type = "image" if suffix in {".jpg", ".jpeg", ".png", ".webp"} else "document"

    storage = LocalFileStorage()
    path = await storage.save(file.filename, content)
    document = Document(
        filename=Path(file.filename).name,
        storage_path=path,
        document_type=document_type,
        mime_type=mime,
        status="uploaded",
        metadata_json={
            "size_bytes": len(content),
            "upload_latency_ms": round((perf_counter() - started) * 1000),
        },
    )
    await DocumentRepository(db).create(document)
    await db.commit()
    return document
