
from app.research_intelligence.router import AdaptiveRetrievalRouter
from app.research_intelligence.fusion import EvidenceFusionEngine
from app.research_intelligence.verifier import ClaimVerifier
from app.reasoning.models import UnifiedEvidence


def ev(eid, source, content, score=0.8):
    return UnifiedEvidence(
        evidence_id=eid,
        source_type=source,
        source_id=eid,
        content=content,
        score=score,
        provenance={},
    )


def test_router_prefers_structured_for_nutrition():
    plan = AdaptiveRetrievalRouter().plan("How much protein is in 100 g tofu?")
    assert "structured" in plan.selected_sources
    assert plan.source_weights["structured"] > plan.source_weights["vector"]


def test_fusion_detects_numeric_conflict():
    evidence = [
        ev("a", "structured", "Tofu contains 8 g protein per 100 g."),
        ev("b", "vector", "The product contains 12 g protein per 100 g."),
    ]
    result = EvidenceFusionEngine().fuse(evidence, query="protein in tofu")
    assert result.conflicts
    assert any(c.conflict_type == "numeric" for c in result.conflicts)


def test_verifier_rejects_unsupported_claim():
    evidence = [ev("a", "structured", "Tofu contains 8 g protein per 100 g.")]
    result = ClaimVerifier().verify(
        "Tofu contains 8 g protein per 100 g. Tofu contains 50 g vitamin C.",
        evidence,
    )
    assert result.unsupported_claim_count >= 1
