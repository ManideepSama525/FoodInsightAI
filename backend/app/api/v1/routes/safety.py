from fastapi import APIRouter
from app.safety.models import AdulterationSignal, Evidence, SafetyAssessment
from app.safety.service import SafetyService

router = APIRouter()
service = SafetyService()

@router.post("/assess", response_model=SafetyAssessment)
async def assess_safety(
    subject: str,
    hazards: list[str] = [],
    controls: list[str] = [],
    evidence: list[Evidence] = [],
):
    return service.assess(subject, hazards, controls, evidence)

@router.post("/adulteration", response_model=AdulterationSignal)
async def assess_adulteration(signal: AdulterationSignal):
    return service.evaluate_adulteration(signal)
