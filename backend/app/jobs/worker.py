from typing import Awaitable, Callable, Any
from .models import Job
from .store import store

class CancellationRequested(Exception):
    pass

def check_cancel(job: Job):
    if getattr(job, "cancel_requested", False):
        raise CancellationRequested("Job cancellation requested.")

async def execute(job: Job, worker: Callable[[Job], Awaitable[dict[str, Any]]]):
    job.update(status="running", progress=5, message="Worker started")
    try:
        check_cancel(job)
        result = await worker(job)
        check_cancel(job)
        job.update(status="completed", progress=100, message="Completed", result=result)
    except CancellationRequested as exc:
        job.update(status="cancelled", progress=100, message="Cancelled", error=str(exc))
    except Exception as exc:
        job.update(status="failed", progress=100, message="Failed", error=str(exc))
