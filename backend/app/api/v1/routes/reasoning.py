from fastapi import APIRouter
from app.reasoning.models import RetrievalSignal
from app.reasoning.context import ReasoningContextBuilder
from app.reasoning.answer_policy import AnswerPolicy

router=APIRouter()
builder=ReasoningContextBuilder()
policy=AnswerPolicy()

@router.post("/context")
async def build_context(
    query: str,
    vector: list[RetrievalSignal]=[],
    lexical: list[RetrievalSignal]=[],
    graph: list[RetrievalSignal]=[],
    structured: list[RetrievalSignal]=[],
    observations: list[dict]=[],
):
    context=builder.build(
        query=query,
        vector=vector,
        lexical=lexical,
        graph=graph,
        structured=structured,
        observations=observations,
    )
    return {
        "context": context,
        "answer_policy": policy.validate(context),
    }
