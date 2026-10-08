import asyncio
from app.api.v1.routes.documents import list_documents
from app.core.database import SessionLocal

async def main():
    async with SessionLocal() as db:
        print("CALLING ROUTE")
        result = await list_documents(
            limit=50,
            offset=0,
            db=db,
        )
        print("ROUTE RESULT TYPE:", type(result))
        print("ROUTE RESULT:", result)
        print("ROUTE DUMP:", result.model_dump())

asyncio.run(main())
