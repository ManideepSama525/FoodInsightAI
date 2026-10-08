from datetime import datetime, timezone
from dataclasses import asdict, dataclass
from typing import Any

@dataclass
class JobEvent:
    event_type: str
    job_id: str
    status: str
    progress: int
    message: str
    timestamp: str
    payload: dict[str, Any] | None = None

def make_event(job, event_type: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    return asdict(JobEvent(event_type, job.id, job.status, job.progress, job.message,
                           datetime.now(timezone.utc).isoformat(), payload))
