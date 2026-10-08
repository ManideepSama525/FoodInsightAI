from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

@dataclass
class Job:
    id: str
    kind: str
    subject_id: str | None = None
    status: str = "queued"
    progress: int = 0
    message: str = "Queued"
    result: dict[str, Any] | None = None
    error: str | None = None
    idempotency_key: str | None = None
    cancel_requested: bool = False
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def update(self, *, status=None, progress=None, message=None, result=None, error=None):
        if status is not None: self.status = status
        if progress is not None: self.progress = max(0, min(100, int(progress)))
        if message is not None: self.message = message
        if result is not None: self.result = result
        if error is not None: self.error = error
        self.updated_at = datetime.now(timezone.utc)

def new_job(kind: str, subject_id: str | None = None) -> Job:
    return Job(id=str(uuid4()), kind=kind, subject_id=subject_id)
