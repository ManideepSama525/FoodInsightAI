from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.research_intelligence.raw_inference import build_foodinsight_prompt


router = APIRouter(prefix="/foodinsight-inference", tags=["foodinsight-inference"])


class FoodInsightPromptRequest(BaseModel):
    question: str = Field(min_length=1)
    evidence: str = ""
    extra_instruction: str = "Give a concise evidence-grounded answer."


class FoodInsightPromptResponse(BaseModel):
    prompt: str


@router.post("/prompt", response_model=FoodInsightPromptResponse)
def build_prompt(request: FoodInsightPromptRequest) -> FoodInsightPromptResponse:
    return FoodInsightPromptResponse(
        prompt=build_foodinsight_prompt(
            request.question,
            request.evidence,
            extra_instruction=request.extra_instruction,
        )
    )
