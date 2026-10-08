
import pytest

from app.research_intelligence.chat_pipeline import ResearchChatPipeline


class FakeProvider:
    model_name = "test-model"


class FakeLLM:
    provider = FakeProvider()

    async def answer(self, message, context):
        from app.llm.models import LLMResponse
        return LLMResponse(
            answer="Lentils contain 9 g protein per 100 g.",
            source_refs=[],
            confidence=0.9,
        )


@pytest.mark.asyncio
async def test_research_pipeline_verifies_generated_claim():
    # Avoid constructing the real Qdrant-backed retrieval service in this unit test.
    # The integration tests cover the actual retrieval adapter separately.
    pipeline = object.__new__(ResearchChatPipeline)
    pipeline.llm = FakeLLM()
    from app.validation.grounding import GroundingValidator
    pipeline.grounding = GroundingValidator()
    from app.research_intelligence.service import ResearchIntelligenceService
    from app.research_intelligence.verifier import ClaimVerifier
    pipeline.research = object.__new__(ResearchIntelligenceService)
    pipeline.research.verifier = ClaimVerifier()

    async def fake_retrieve(**kwargs):
        from app.research_intelligence.models import EvidenceFusionResult, FusedEvidence, RetrievalPlan
        return {
            "plan": RetrievalPlan(
                query=kwargs["query"],
                intent="nutrition_lookup",
                source_weights={"structured": 0.8, "vector": 0.2},
                selected_sources=["structured", "vector"],
            ),
            "retrieval": {
                "vector_count": 0,
                "lexical_count": 0,
                "structured_count": 1,
                "graph_count": 0,
            },
            "fusion": EvidenceFusionResult(
                evidence=[FusedEvidence(
                    evidence_id="structured:lentils",
                    source_type="structured",
                    source_id="lentils",
                    content="Lentils contain 9 g protein per 100 g.",
                    retrieval_score=1.0,
                    reliability=0.95,
                    final_score=0.95,
                    provenance={},
                )],
                conflicts=[],
                uncertainty=[],
            ),
            "warnings": [],
        }

    pipeline.research.retrieve_and_fuse = fake_retrieve
    result = await pipeline.answer("How much protein is in lentils?")
    assert result["research"]["verification"]["unsupported_claim_count"] == 0
    assert result["research"]["verification"]["answer_allowed"] is True
