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
        print("DOCUMENT COUNT:", len(documents))

        for document in documents:
            print(
                document.id,
                document.filename,
                document.document_type,
                document.status,
            )


asyncio.run(main())