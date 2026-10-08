from pydantic import BaseModel, Field

class RetrievalSignal(BaseModel):
    source_type: str
    source_id: str
    score: float = Field(ge=0)
    content: str
    metadata: dict = {}

class UnifiedEvidence(BaseModel):
    evidence_id: str
    source_type: str
    source_id: str
    content: str
    score: float
    provenance: dict = {}

class ReasoningContext(BaseModel):
    query: str
    evidence: list[UnifiedEvidence] = []
    graph_relations: list[dict] = []
    structured_data: list[dict] = []
    observations: list[dict] = []
    uncertainty: list[str] = []
