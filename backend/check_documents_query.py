import asyncio
from sqlalchemy import select
from app.core.database import SessionLocal
from app.models.entities import Document

async def main():
    async with SessionLocal() as session:
        result = await session.execute(
            select(Document)
            .order_by(Document.created_at.desc())
            .limit(50)
            .offset(0)
        )
        documents = list(result.scalars().all())

        print("QUERY SUCCESS")
        print("COUNT:", len(documents))

        for document in documents:
            print("ID:", document.id)
            print("FILENAME:", document.filename)
            print("TYPE:", document.document_type)
            print("MIME:", document.mime_type)
            print("STATUS:", document.status)
            print("SOURCE:", document.source)
            print("CREATED:", document.created_at)

asyncio.run(main())
