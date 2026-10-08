from datetime import datetime
from pydantic import BaseModel

class JobOut(BaseModel):
    id: str
    kind: str
    subject_id: str | None
    status: str
    progress: int
    message: str
    result: dict | None = None
    error: str | None = None
    idempotency_key: str | None = None
    cancel_requested: bool = False
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_job(cls, job):
        return cls(
            id=job.id, kind=job.kind, subject_id=job.subject_id,
            status=job.status, progress=job.progress, message=job.message,
            result=job.result, error=job.error,
            created_at=job.created_at, updated_at=job.updated_at,
        )
