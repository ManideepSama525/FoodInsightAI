from dataclasses import dataclass
import asyncio
import os

@dataclass(frozen=True)
class WorkerSettings:
    redis_url: str = os.getenv("FOODINSIGHT_REDIS_URL", "redis://redis:6379/0")
    concurrency: int = int(os.getenv("FOODINSIGHT_WORKER_CONCURRENCY", "4"))
    queue_name: str = os.getenv("FOODINSIGHT_JOB_QUEUE", "foodinsight.jobs")
    dead_letter_queue: str = os.getenv("FOODINSIGHT_DLQ", "foodinsight.jobs.dlq")

settings = WorkerSettings()
semaphore = asyncio.Semaphore(settings.concurrency)
