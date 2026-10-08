from app.llm.models import LLMResponse, LLMSourceRef
from app.rag.context import CitationRecord
from app.validation.grounding import GroundingValidator

def test_invalid_citation_is_removed():
    response = LLMResponse(answer="Evidence", source_refs=[LLMSourceRef(source_index=9)])
    citations = [CitationRecord("doc", "file.pdf", 2, "d", "c")]
    validated, warnings = GroundingValidator().validate(response, citations, "Evidence")
    assert validated.source_refs == []
    assert "invalid_source_reference" in warnings

def test_no_context_forces_insufficient_evidence():
    response = LLMResponse(answer="Invented", source_refs=[])
    validated, warnings = GroundingValidator().validate(response, [], "")
    assert validated.uncertainty == "insufficient_evidence"
    assert "insufficient_evidence" in warnings
