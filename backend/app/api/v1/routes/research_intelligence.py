
from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.reasoning.models import UnifiedEvidence
from app.research_intelligence.service import ResearchIntelligenceService

router = APIRouter()
service = ResearchIntelligenceService()


class PlanRequest(BaseModel):
    query: str
    has_image: bool = False


class EvidenceRequest(BaseModel):
    query: str
    evidence: list[UnifiedEvidence] = []
    top_k: int = Field(default=8, ge=1, le=50)


class VerificationRequest(BaseModel):
    answer: str
    evidence: list[UnifiedEvidence] = []
    conflicts: list[dict] = []


@router.post("/plan")
async def plan(request: PlanRequest):
    return service.plan(request.query, request.has_image)


@router.post("/analyze-evidence")
async def analyze_evidence(request: EvidenceRequest):
    return service.analyze_evidence(request.query, request.evidence, request.top_k)


@router.post("/verify")
async def verify(request: VerificationRequest):
    return service.verify(request.answer, request.evidence, request.conflicts)


class RetrievalRequest(BaseModel):
    query: str
    has_image: bool = False
    document_ids: list[str] = []
    top_k: int = Field(default=8, ge=1, le=50)


@router.post("/retrieve-and-fuse")
async def retrieve_and_fuse(request: RetrievalRequest):
    return await service.retrieve_and_fuse(
        query=request.query,
        has_image=request.has_image,
        document_ids=request.document_ids or None,
        top_k=request.top_k,
    )
