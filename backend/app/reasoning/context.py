from app.reasoning.models import (
    RetrievalSignal,
    ReasoningContext,
)
from app.reasoning.hybrid import HybridRetriever
from app.research_intelligence.fusion import EvidenceFusionEngine

class ReasoningContextBuilder:
    def __init__(self, retriever: HybridRetriever | None = None):
        self.retriever = retriever or HybridRetriever()
        self.fusion = EvidenceFusionEngine()

    def build(
        self,
        query: str,
        vector: list[RetrievalSignal] = [],
        lexical: list[RetrievalSignal] = [],
        graph: list[RetrievalSignal] = [],
        structured: list[RetrievalSignal] = [],
        observations: list[dict] = [],
    ) -> ReasoningContext:
        raw_evidence = self.retriever.merge(vector, lexical, graph, structured)
        fusion = self.fusion.fuse(raw_evidence, query=query)
        evidence = [
            type(item)(
                evidence_id=item.evidence_id,
                source_type=item.source_type,
                source_id=item.source_id,
                content=item.content,
                score=item.final_score,
                provenance=item.provenance,
            )
            for item in fusion.evidence
        ]
        uncertainty = list(fusion.uncertainty)
        if not evidence:
            uncertainty.append("No retrieval evidence was available.")
        if observations:
            uncertainty.append(
                "Visual observations are treated as observations, not authoritative food facts."
            )
        return ReasoningContext(
            query=query,
            evidence=evidence,
            graph_relations=[e.provenance for e in evidence if e.source_type == "graph"],
            structured_data=[e.provenance for e in evidence if e.source_type == "structured"],
            observations=observations,
            uncertainty=uncertainty,
        )
