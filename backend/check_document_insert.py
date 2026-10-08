import asyncio
from app.core.database import SessionLocal
from app.models.entities import Document

async def main():
    async with SessionLocal() as session:
        document = Document(
            filename="orm_test.txt",
            storage_path="/app/data/uploads/orm_test.txt",
            document_type="document",
            mime_type="text/plain",
            status="uploaded",
            metadata_json={"test": True},
        )
        session.add(document)
        await session.flush()
        await session.commit()
        print("INSERT SUCCESS")
        print("DOCUMENT ID:", document.id)

asyncio.run(main())
