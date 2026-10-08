import asyncio
from typing import Awaitable, Callable, Any
from .models import Job
from .store import store
from .lifecycle import WorkerLifecycle

_lifecycle = WorkerLifecycle()

def enqueue(job: Job, worker: Callable[[Job], Awaitable[dict[str, Any]]], idempotency_key: str | None = None) -> Job:
    if idempotency_key:
        for existing in store.list():
            if getattr(existing, "idempotency_key", None) == idempotency_key:
                return existing
        job.idempotency_key = idempotency_key
    store.create(job)
    asyncio.create_task(_lifecycle.execute(job, worker))
    return job

def cancel(job_id: str) -> Job | None:
    job = store.get(job_id)
    if not job:
        return None
    job.cancel_requested = True
    return job

def shutdown():
    _lifecycle.shutdown()
