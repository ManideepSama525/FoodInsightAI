from app.safety.models import FeedbackRecord

class FeedbackService:
    def __init__(self):
        self._records: list[FeedbackRecord] = []

    def add(self, record: FeedbackRecord) -> FeedbackRecord:
        self._records.append(record)
        return record

    def for_subject(self, subject_id: str) -> list[FeedbackRecord]:
        return [r for r in self._records if r.subject_id == subject_id]
