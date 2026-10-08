from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.repositories.documents import DocumentRepository
from app.schemas.documents import DocumentList, DocumentOut

router = APIRouter()


@router.get("", response_model=DocumentList)
async def list_documents(
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    repo = DocumentRepository(db)
    items = await repo.list(limit=limit, offset=offset)

    output = [
        DocumentOut.model_validate(document)
        for document in items
    ]

    return DocumentList(
        items=output,
        total=len(output),
    )


@router.get("/{document_id}", response_model=DocumentOut)
async def get_document(
    document_id: str,
    db: AsyncSession = Depends(get_db),
):
    document = await DocumentRepository(db).get(document_id)

    if not document:
        raise HTTPException(status_code=404, detail="Document not found.")

    return DocumentOut.model_validate(document)
