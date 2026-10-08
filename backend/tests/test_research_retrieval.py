
import pytest

from app.research_intelligence.retrieval import ResearchRetrievalService


class FakeRAG:
    async def retrieve_context(self, query, document_ids=None, top_k=8, rerank_top_k=8):
        return "", [], [{
            "chunk_id": "docchunk-1",
            "document_id": "doc-1",
            "page": 2,
            "score": 0.9,
            "text": "Research evidence about lentils and protein.",
        }]


@pytest.mark.asyncio
async def test_retrieval_connects_structured_and_graph():
    service = ResearchRetrievalService(rag=FakeRAG())
    result = await service.retrieve("protein in lentils", top_k=5)

    assert result.plan.source_weights["structured"] > result.plan.source_weights["vector"]
    assert result.structured
    assert result.vector


@pytest.mark.asyncio
async def test_retrieval_connects_graph_for_relationship_query():
    service = ResearchRetrievalService(rag=FakeRAG())
    result = await service.retrieve("relationship between lentils and protein", top_k=5)

    assert result.graph
    assert any("has_nutrient" in x.content for x in result.graph)
