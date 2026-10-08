import asyncio
from sqlalchemy import select
from app.core.database import SessionLocal
from app.models.entities import Document
from app.schemas.documents import DocumentOut, DocumentList

async def main():
    async with SessionLocal() as session:
        result = await session.execute(
            select(Document)
            .order_by(Document.created_at.desc())
            .limit(50)
            .offset(0)
        )
        documents = list(result.scalars().all())

        print("ORM COUNT:", len(documents))

        for document in documents:
            item = DocumentOut.model_validate(document)
            print("DOCUMENTOUT SUCCESS:", item.model_dump())

        result_model = DocumentList(
            items=[DocumentOut.model_validate(d) for d in documents],
            total=len(documents),
        )

        print("DOCUMENTLIST SUCCESS:")
        print(result_model.model_dump())

asyncio.run(main())
