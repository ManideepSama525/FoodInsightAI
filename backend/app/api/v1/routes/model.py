
from fastapi import APIRouter
from pydantic import BaseModel, Field
from time import perf_counter

router = APIRouter()


class ModelBenchmarkRequest(BaseModel):
    model_id: str
    prompt: str = "State the role of evidence verification in FoodInsightAI."
    max_new_tokens: int = Field(default=64, ge=1, le=512)


@router.post("/benchmark/local")
async def benchmark_local_model(request: ModelBenchmarkRequest):
    """Minimal local-model benchmark.

    The endpoint imports the provider only when invoked. It measures generation
    latency and reports the configured model; it does not expose hidden model
    reasoning.
    """
    from app.llm.local.config import LocalModelConfig
    from app.llm.local.provider import LocalTransformersProvider

    provider = LocalTransformersProvider(
        LocalModelConfig(
            model_id=request.model_id,
            max_new_tokens=request.max_new_tokens,
            temperature=0.0,
            top_p=1.0,
            load_in_4bit=True,
            trust_remote_code=False,
        )
    )

    started = perf_counter()
    answer = await provider.answer(
        request.prompt,
        "FoodInsightAI evidence verification improves grounding.",
    )
    elapsed = (perf_counter() - started) * 1000

    return {
        "model_id": request.model_id,
        "answer": answer,
        "latency_ms": round(elapsed, 2),
        "max_new_tokens": request.max_new_tokens,
    }
