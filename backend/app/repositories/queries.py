from sqlalchemy.ext.asyncio import AsyncSession
from app.models.entities import QueryLog, ResponseLog, Citation

class QueryRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def log_query(self, query: QueryLog) -> QueryLog:
        self.session.add(query)
        await self.session.flush()
        return query

    async def log_response(self, response: ResponseLog) -> ResponseLog:
        self.session.add(response)
        await self.session.flush()
        return response

    async def add_citation(self, citation: Citation) -> Citation:
        self.session.add(citation)
        await self.session.flush()
        return citation
