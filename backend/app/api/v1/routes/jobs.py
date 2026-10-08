from fastapi import APIRouter, HTTPException
from app.jobs.store import store
from app.jobs.service import cancel
from app.schemas.jobs import JobOut

router = APIRouter()

@router.get("/{job_id}", response_model=JobOut)
async def get_job(job_id: str):
    job = store.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")
    return JobOut.from_job(job)

@router.post("/{job_id}/cancel", response_model=JobOut)
async def cancel_job(job_id: str):
    job = cancel(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")
    return JobOut.from_job(job)

@router.get("", response_model=list[JobOut])
async def list_jobs():
    return [JobOut.from_job(job) for job in store.list()]
