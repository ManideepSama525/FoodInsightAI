from fastapi import APIRouter
from app.safety.models import FeedbackRecord
from app.feedback.service import FeedbackService

router = APIRouter()
service = FeedbackService()

@router.post("", response_model=FeedbackRecord)
async def add_feedback(record: FeedbackRecord):
    return service.add(record)

@router.get("/{subject_id}", response_model=list[FeedbackRecord])
async def get_feedback(subject_id: str):
    return service.for_subject(subject_id)
