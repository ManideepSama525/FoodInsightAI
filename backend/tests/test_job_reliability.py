import asyncio

from app.jobs.models import new_job
from app.jobs.reliability import RetryPolicy
from app.jobs.lifecycle import WorkerLifecycle

def test_retry_policy_is_bounded():
    p = RetryPolicy(max_attempts=3, base_delay_seconds=1, max_delay_seconds=2, jitter=0)
    assert p.delay(1) == 1
    assert p.delay(2) == 2
    assert p.delay(5) == 2

def test_worker_recovers_after_transient_failure():
    attempts = {"n": 0}
    async def worker(job):
        attempts["n"] += 1
        if attempts["n"] < 2:
            raise RuntimeError("transient")
        return {"ok": True}

    async def run():
        job = new_job("test")
        await WorkerLifecycle(RetryPolicy(max_attempts=3, base_delay_seconds=0, jitter=0)).execute(job, worker)
        return job

    job = asyncio.run(run())
    assert attempts["n"] == 2
    assert job.status == "completed"
    assert job.result == {"ok": True}
