from pydantic import BaseModel, Field

class Evidence(BaseModel):
    evidence_id: str
    topic: str
    statement: str
    source: str
    source_type: str
    confidence: float = Field(ge=0, le=1)
    jurisdiction: str | None = None
    effective_date: str | None = None

class SafetyAssessment(BaseModel):
    subject: str
    status: str
    hazards: list[str] = []
    controls: list[str] = []
    evidence: list[Evidence] = []
    uncertainty: list[str] = []

class AdulterationSignal(BaseModel):
    signal_id: str
    subject: str
    indicator: str
    observed_value: str
    threshold_or_reference: str | None = None
    status: str
    evidence: list[Evidence] = []

class TraceEvent(BaseModel):
    event_id: str
    subject_id: str
    event_type: str
    actor: str
    timestamp: str
    location: str | None = None
    metadata: dict = {}

class FeedbackRecord(BaseModel):
    feedback_id: str
    subject_id: str
    rating: int = Field(ge=1, le=5)
    comment: str | None = None
    created_at: str
    tags: list[str] = []
