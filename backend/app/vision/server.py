from __future__ import annotations

from fastapi import FastAPI
from pydantic import BaseModel

from app.vision.local_provider import LocalVisionProvider


app = FastAPI(title="FoodInsightAI Local Vision Server")

provider = LocalVisionProvider()


class AnalyzeRequest(BaseModel):
    image_path: str
    question: str | None = None


class AnalyzeResponse(BaseModel):
    result: dict


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "service": "foodinsightai-local-vision",
        "model": provider.model_name,
        "cuda": __import__("torch").cuda.is_available(),
    }


@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze(request: AnalyzeRequest):
    result = await provider.analyze(
        image_path=request.image_path,
        question=request.question,
    )

    return AnalyzeResponse(
        result=result.model_dump(),
    )
