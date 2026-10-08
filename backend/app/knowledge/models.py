from pydantic import BaseModel, Field

class KnowledgeEntity(BaseModel):
    entity_id: str
    entity_type: str
    canonical_name: str
    aliases: list[str] = []
    attributes: dict = {}
    source_ids: list[str] = []

class KnowledgeRelation(BaseModel):
    relation_id: str
    subject_id: str
    predicate: str
    object_id: str
    confidence: float = Field(ge=0, le=1)
    source_ids: list[str] = []
    metadata: dict = {}

class ResolutionCandidate(BaseModel):
    entity_id: str
    canonical_name: str
    entity_type: str
    score: float = Field(ge=0, le=1)
    matched_on: list[str] = []

class ResolutionResult(BaseModel):
    query: str
    candidates: list[ResolutionCandidate] = []
    resolved_entity_id: str | None = None
    resolution_status: str
