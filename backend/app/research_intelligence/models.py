
from pydantic import BaseModel, Field
from typing import Literal


class RetrievalPlan(BaseModel):
    query: str
    intent: str
    source_weights: dict[str, float]
    selected_sources: list[str]
    rationale: list[str] = []


class EvidenceReliability(BaseModel):
    evidence_id: str
    relevance: float = Field(ge=0, le=1)
    authority: float = Field(ge=0, le=1)
    freshness: float = Field(ge=0, le=1)
    consistency: float = Field(ge=0, le=1)
    reliability: float = Field(ge=0, le=1)


class EvidenceConflict(BaseModel):
    conflict_id: str
    evidence_ids: list[str]
    conflict_type: Literal[
        "numeric",
        "serving_size",
        "food_form",
        "temporal",
        "source_disagreement",
        "semantic",
        "unknown",
    ]
    severity: float = Field(ge=0, le=1)
    explanation: str
    resolution: str


class FusedEvidence(BaseModel):
    evidence_id: str
    source_type: str
    source_id: str
    content: str
    retrieval_score: float
    reliability: float
    final_score: float
    provenance: dict = {}


class EvidenceFusionResult(BaseModel):
    evidence: list[FusedEvidence] = []
    conflicts: list[EvidenceConflict] = []
    uncertainty: list[str] = []


class VerifiedClaim(BaseModel):
    claim: str
    status: Literal["supported", "contradicted", "unsupported", "uncertain"]
    support_score: float = Field(ge=0, le=1)
    evidence_ids: list[str] = []
    explanation: str


class VerificationResult(BaseModel):
    claims: list[VerifiedClaim] = []
    answer_allowed: bool
    unsupported_claim_count: int
    uncertainty: list[str] = []
