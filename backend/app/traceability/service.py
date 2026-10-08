from app.safety.models import TraceEvent

class TraceabilityService:
    def __init__(self):
        self._events: list[TraceEvent] = []

    def add_event(self, event: TraceEvent) -> TraceEvent:
        self._events.append(event)
        return event

    def history(self, subject_id: str) -> list[TraceEvent]:
        return [e for e in self._events if e.subject_id == subject_id]
