from app.reasoning.models import RetrievalSignal, UnifiedEvidence

class HybridRetriever:
    def merge(
        self,
        vector: list[RetrievalSignal] = [],
        lexical: list[RetrievalSignal] = [],
        graph: list[RetrievalSignal] = [],
        structured: list[RetrievalSignal] = [],
    ) -> list[UnifiedEvidence]:
        # Reciprocal-rank-style normalization keeps heterogeneous scores
        # comparable without pretending they share identical semantics.
        buckets = {
            "vector": vector,
            "lexical": lexical,
            "graph": graph,
            "structured": structured,
        }
        merged: dict[tuple[str,str], UnifiedEvidence] = {}
        for source_type, items in buckets.items():
            for rank, item in enumerate(items, start=1):
                rank_score = 1.0 / (50 + rank)
                combined = max(item.score, 0.0) + rank_score
                key = (item.source_type, item.source_id)
                candidate = UnifiedEvidence(
                    evidence_id=f"{item.source_type}:{item.source_id}",
                    source_type=item.source_type,
                    source_id=item.source_id,
                    content=item.content,
                    score=combined,
                    provenance={
                        **item.metadata,
                        "retrieval_channel": source_type,
                        "rank": rank,
                    },
                )
                if key not in merged or candidate.score > merged[key].score:
                    merged[key] = candidate
        return sorted(merged.values(), key=lambda x: x.score, reverse=True)
