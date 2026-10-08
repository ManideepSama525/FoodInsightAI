from fastapi import APIRouter
from app.safety.models import TraceEvent
from app.traceability.service import TraceabilityService

router = APIRouter()
service = TraceabilityService()

@router.post("/events", response_model=TraceEvent)
async def add_event(event: TraceEvent):
    return service.add_event(event)

@router.get("/history/{subject_id}", response_model=list[TraceEvent])
async def history(subject_id: str):
    return service.history(subject_id)
