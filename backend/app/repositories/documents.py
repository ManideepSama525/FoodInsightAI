from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.entities import Document, DocumentChunk

class DocumentRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, document: Document) -> Document:
        self.session.add(document)
        await self.session.flush()
        return document

    async def get(self, document_id: str) -> Document | None:
        return await self.session.get(Document, document_id)

    async def list(self, limit: int = 50, offset: int = 0) -> list[Document]:
        result = await self.session.execute(
            select(Document).order_by(Document.created_at.desc()).limit(limit).offset(offset)
        )
        return list(result.scalars().all())

    async def add_chunk(self, chunk: DocumentChunk) -> DocumentChunk:
        self.session.add(chunk)
        await self.session.flush()
        return chunk
