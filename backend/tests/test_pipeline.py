import asyncio
from app.orchestration.models import PipelineRequest
from app.orchestration.pipeline import ProductionPipeline

def test_pipeline_without_evidence_is_explicit():
    result=asyncio.run(
        ProductionPipeline().run(PipelineRequest(query="unsupported demo query"))
    )
    assert result.grounded is False
    assert result.stages[-1].name == "respond"
    assert result.uncertainty

def test_pipeline_does_not_expose_reasoning_trace():
    result=asyncio.run(
        ProductionPipeline().run(PipelineRequest(query="demo"))
    )
    payload=result.model_dump()
    assert "chain_of_thought" not in payload
    assert "reasoning_trace" not in payload
