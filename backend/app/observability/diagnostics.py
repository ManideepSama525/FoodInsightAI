from datetime import datetime, timezone
from app.jobs.store import store
from app.jobs.runtime import settings
from app.observability.metrics import metrics
from app.observability.sre import evaluate

def snapshot() -> dict:
    metric_snapshot = metrics.snapshot()
    jobs = list(store.list(limit=100))
    counts = {}
    for job in jobs:
        counts[job.status] = counts.get(job.status, 0) + 1
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "sre": evaluate(metric_snapshot),
        "metrics": metric_snapshot,
        "jobs": counts,
        "worker": {
            "concurrency": settings.concurrency,
            "queue": settings.queue_name,
            "dead_letter_queue": settings.dead_letter_queue,
        },
    }
