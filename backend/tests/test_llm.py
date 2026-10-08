import asyncio
from app.llm.orchestrator import LLMOrchestrator
from app.llm.providers import MockLLMProvider

def test_mock_llm_returns_validated_output():
    async def run():
        result = await LLMOrchestrator(MockLLMProvider()).answer(
            "What does the document say?",
            "[SOURCE 1]\nTitle: Test\nSource: test.txt\nPage: 1\nEvidence:\nSpinach contains iron."
        )
        return result

    result = asyncio.run(run())
    assert result.source_refs[0].source_index == 1
    assert "Spinach" in result.answer
