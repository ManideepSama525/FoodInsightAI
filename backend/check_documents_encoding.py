import asyncio
from fastapi.encoders import jsonable_encoder
from app.api.v1.routes.documents import list_documents
from app.core.database import SessionLocal

async def main():
    async with SessionLocal() as db:
        result = await list_documents(limit=50, offset=0, db=db)

        print("ROUTE RETURNED")

        encoded = jsonable_encoder(result)

        print("ENCODING SUCCESS")
        print(encoded)

asyncio.run(main())
