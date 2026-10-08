
import pytest

from app.research_intelligence.feedback_loop import VerificationFeedbackLoop
from app.research_intelligence.verifier import ClaimVerifier
from app.reasoning.models import UnifiedEvidence


def evidence(text):
    return [UnifiedEvidence(
        evidence_id="e1",
        source_type="structured",
        source_id="food-1",
        content=text,
        score=1.0,
        provenance={},
    )]


class FakeLLM:
    model_name = "test"

    def __init__(self):
        # The initial answer is supplied directly to the loop. The first
        # generation requested by the loop is therefore the corrected answer.
        self.calls = 1

    async def answer(self, query, context):
        from app.llm.models import LLMResponse
        self.calls += 1
        if self.calls == 1:
            return LLMResponse(
                answer="Lentils contain 50 g protein per 100 g.",
                source_refs=[],
            )
        return LLMResponse(
            answer="Lentils contain 9 g protein per 100 g.",
            source_refs=[],
        )


class FakeOrchestrator:
    provider = type("Provider", (), {"model_name": "test"})()

    def __init__(self):
        self.provider = type("Provider", (), {"model_name": "test"})()
        self.fake = FakeLLM()

    async def answer(self, query, context):
        return await self.fake.answer(query, context)


@pytest.mark.asyncio
async def test_feedback_loop_accepts_supported_answer():
    llm = FakeOrchestrator()
    loop = VerificationFeedbackLoop(llm=llm, verifier=ClaimVerifier(), max_attempts=2)
    result = await loop.run(
        "How much protein is in lentils?",
        "Lentils contain 9 g protein per 100 g.",
        evidence("Lentils contain 9 g protein per 100 g."),
    )
    assert result.status == "accepted"
    assert len(result.attempts) == 1


@pytest.mark.asyncio
async def test_feedback_loop_requests_revision_and_accepts_corrected_answer():
    llm = FakeOrchestrator()
    loop = VerificationFeedbackLoop(llm=llm, verifier=ClaimVerifier(), max_attempts=2)
    result = await loop.run(
        "How much protein is in lentils?",
        "Lentils contain 50 g protein per 100 g.",
        evidence("Lentils contain 9 g protein per 100 g."),
    )
    assert result.status == "accepted"
    assert len(result.attempts) == 2
    assert result.attempts[0].status == "needs_revision"
