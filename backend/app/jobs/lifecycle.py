import asyncio
from typing import Awaitable, Callable, Any
from .models import Job
from .worker import CancellationRequested, check_cancel
from .reliability import RetryPolicy, backoff
from .heartbeat import Heartbeat
from app.observability.metrics import metrics

class WorkerLifecycle:
    def __init__(self, retry_policy: RetryPolicy | None = None):
        self.retry_policy = retry_policy or RetryPolicy()
        self.stopping = False
        self.heartbeat = Heartbeat()

    def shutdown(self):
        self.stopping = True

    async def execute(self, job: Job, worker: Callable[[Job], Awaitable[dict[str, Any]]]):
        job.update(status="running", progress=5, message="Worker started")
        metrics.increment("jobs_started_total")
        for attempt in range(1, self.retry_policy.max_attempts + 1):
            if self.stopping:
                job.update(status="cancelled", progress=100, message="Worker shutting down")
                return
            try:
                check_cancel(job)
                self.heartbeat.beat()
                result = await worker(job)
                check_cancel(job)
                job.update(status="completed", progress=100, message="Completed", result=result)
                metrics.increment("jobs_completed_total")
                return
            except CancellationRequested as exc:
                job.update(status="cancelled", progress=100, message="Cancelled", error=str(exc))
                metrics.increment("jobs_cancelled_total")
                return
            except Exception as exc:
                self.heartbeat.beat()
                if attempt >= self.retry_policy.max_attempts:
                    job.update(status="failed", progress=100, message="Failed after retries", error=str(exc))
                    metrics.increment("jobs_failed_total")
                    return
                job.update(message=f"Retrying ({attempt}/{self.retry_policy.max_attempts - 1})")
                await backoff(self.retry_policy, attempt)
