from app.safety.models import FeedbackRecord, TraceEvent
from app.traceability.service import TraceabilityService
from app.feedback.service import FeedbackService

def test_traceability_filters_by_subject():
    service = TraceabilityService()
    service.add_event(TraceEvent(
        event_id="1", subject_id="food-1", event_type="received",
        actor="supplier", timestamp="2026-01-01T00:00:00Z"
    ))
    service.add_event(TraceEvent(
        event_id="2", subject_id="food-2", event_type="received",
        actor="supplier", timestamp="2026-01-01T00:00:00Z"
    ))
    assert len(service.history("food-1")) == 1

def test_feedback_filters_by_subject():
    service = FeedbackService()
    service.add(FeedbackRecord(
        feedback_id="f1", subject_id="food-1", rating=4,
        created_at="2026-01-01T00:00:00Z"
    ))
    assert len(service.for_subject("food-1")) == 1
