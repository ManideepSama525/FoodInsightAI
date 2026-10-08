
from __future__ import annotations

from .router import AdaptiveRetrievalRouter
from .fusion import EvidenceFusionEngine
from .verifier import ClaimVerifier
from .retrieval import ResearchRetrievalService
from .models import RetrievalPlan, EvidenceFusionResult, VerificationResult


class ResearchIntelligenceService:
    def __init__(self):
        self.router = AdaptiveRetrievalRouter()
        self.fusion = EvidenceFusionEngine()
        self.verifier = ClaimVerifier()
        self.retrieval = ResearchRetrievalService()

    def plan(self, query: str, has_image: bool = False) -> RetrievalPlan:
        return self.router.plan(query, has_image=has_image)

    async def retrieve_and_fuse(
        self,
        query: str,
        has_image: bool = False,
        document_ids: list[str] | None = None,
        top_k: int = 8,
    ):
        result = await self.retrieval.retrieve(
            query=query,
            has_image=has_image,
            document_ids=document_ids,
            top_k=top_k,
        )
        raw = self.fusion.fuse(
            evidence=[
                *self._to_unified(result.vector),
                *self._to_unified(result.lexical),
                *self._to_unified(result.structured),
                *self._to_unified(result.graph),
            ],
            top_k=top_k,
            query=query,
        )
        return {
            "plan": result.plan,
            "retrieval": {
                "vector_count": len(result.vector),
                "lexical_count": len(result.lexical),
                "structured_count": len(result.structured),
                "graph_count": len(result.graph),
            },
            "fusion": raw,
            "warnings": result.warnings,
        }

    def analyze_evidence(self, query: str, evidence, top_k: int = 8) -> EvidenceFusionResult:
        return self.fusion.fuse(evidence=evidence, top_k=top_k, query=query)

    async def verify(self, answer: str, evidence, conflicts=None, numerical_calculation=None) -> VerificationResult:
        return await self.verifier.verify(answer=answer, evidence=evidence, conflicts=conflicts, numerical_calculation=numerical_calculation)


    def comparison_correction(self, claim: str, evidence):
        return self.verifier.comparison_correction(
            claim=claim,
            evidence=evidence,
        )
    @staticmethod
    def _to_unified(signals):
        from app.reasoning.models import UnifiedEvidence
        return [
            UnifiedEvidence(
                evidence_id=f"{s.source_type}:{s.source_id}",
                source_type=s.source_type,
                source_id=s.source_id,
                content=s.content,
                score=s.score,
                provenance=s.metadata,
            )
            for s in signals
        ]

