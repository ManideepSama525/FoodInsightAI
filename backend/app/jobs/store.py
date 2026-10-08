from typing import Iterable
from .models import Job

class JobStore:
    def __init__(self):
        self._jobs: dict[str, Job] = {}

    def create(self, job: Job) -> Job:
        self._jobs[job.id] = job
        return job

    def get(self, job_id: str) -> Job | None:
        return self._jobs.get(job_id)

    def list(self, limit: int = 50) -> Iterable[Job]:
        return list(self._jobs.values())[-limit:]

store = JobStore()
