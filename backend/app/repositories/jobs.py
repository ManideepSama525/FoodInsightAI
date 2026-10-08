from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.entities import JobRecord

class JobRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get(self, job_id: str):
        return await self.db.get(JobRecord, job_id)

    async def by_idempotency_key(self, key: str):
        result = await self.db.execute(select(JobRecord).where(JobRecord.idempotency_key == key))
        return result.scalar_one_or_none()

    async def create(self, job: JobRecord):
        self.db.add(job)
        await self.db.flush()
        return job

    async def update(self, job: JobRecord, **fields):
        for key, value in fields.items():
            setattr(job, key, value)
        await self.db.flush()
        return job
