
from __future__ import annotations

from .models import EvidenceReliability
from app.reasoning.models import UnifiedEvidence


class EvidenceReliabilityScorer:
    """Transparent v0 evidence scorer.

    Scores are intentionally explainable and bounded. They provide a baseline
    for later supervised learning.
    """

    AUTHORITY = {
        "structured": 0.95,
        "graph": 0.88,
        "vector": 0.75,
        "lexical": 0.65,
        "observation": 0.45,
    }

    def score(
        self,
        evidence: UnifiedEvidence,
        query: str,
        peer_evidence: list[UnifiedEvidence],
    ) -> EvidenceReliability:
        relevance = max(0.0, min(1.0, evidence.score))
        authority = self.AUTHORITY.get(evidence.source_type, 0.50)

        metadata = evidence.provenance or {}
        freshness = float(metadata.get("freshness_score", 0.75))
        freshness = max(0.0, min(1.0, freshness))

        consistency = self._consistency(evidence, peer_evidence)

        reliability = (
            0.40 * relevance
            + 0.25 * authority
            + 0.15 * freshness
            + 0.20 * consistency
        )

        return EvidenceReliability(
            evidence_id=evidence.evidence_id,
            relevance=round(relevance, 4),
            authority=round(authority, 4),
            freshness=round(freshness, 4),
            consistency=round(consistency, 4),
            reliability=round(max(0.0, min(1.0, reliability)), 4),
        )

    def _consistency(self, evidence: UnifiedEvidence, peers: list[UnifiedEvidence]) -> float:
        if not peers:
            return 0.75

        tokens = set(evidence.content.lower().split())
        overlaps = []
        for other in peers:
            if other.evidence_id == evidence.evidence_id:
                continue
            other_tokens = set(other.content.lower().split())
            if not tokens or not other_tokens:
                continue
            overlaps.append(len(tokens & other_tokens) / max(1, len(tokens | other_tokens)))

        return max(0.35, min(1.0, 0.55 + (sum(overlaps) / len(overlaps) if overlaps else 0.20)))
