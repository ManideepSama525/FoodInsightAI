from __future__ import annotations

from fastapi import FastAPI
from pydantic import BaseModel

from app.llm.local.config import LocalModelConfig
from app.llm.local.provider import LocalTransformersProvider


app = FastAPI(title="FoodInsightAI Local Model Server")


class GenerateRequest(BaseModel):
    question: str
    context: str = ""
    max_new_tokens: int = 128


class GenerateResponse(BaseModel):
    answer: str
    model: str


config = LocalModelConfig(
    model_id=(
        r"FoodInsightAI_FoodInsightLM_V0_2"
        r"\artifacts\foodinsight_qwen3_1.7b_v03_qlora\checkpoint-5752"
    ),
    max_new_tokens=128,
    temperature=0.0,
    top_p=1.0,
    load_in_4bit=True,
    trust_remote_code=False,
)

provider = LocalTransformersProvider(config)


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "service": "foodinsightai-local-model",
        "model": provider.model_name,
    }


@app.post("/generate", response_model=GenerateResponse)
async def generate(request: GenerateRequest):
    answer = await provider.answer(
        question=request.question,
        context=request.context,
    )

    return GenerateResponse(
        answer=answer,
        model=provider.model_name,
    )