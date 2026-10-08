
from __future__ import annotations

from .models import EvidenceFusionResult, FusedEvidence
from .reliability import EvidenceReliabilityScorer
from .conflict import ConflictDetector
from app.reasoning.models import UnifiedEvidence


class EvidenceFusionEngine:
    def __init__(
        self,
        scorer: EvidenceReliabilityScorer | None = None,
        conflict_detector: ConflictDetector | None = None,
    ):
        self.scorer = scorer or EvidenceReliabilityScorer()
        self.conflict_detector = conflict_detector or ConflictDetector()

    def fuse(
        self,
        evidence: list[UnifiedEvidence],
        top_k: int = 8,
        query: str = "",
    ) -> EvidenceFusionResult:
        conflicts = self.conflict_detector.detect(evidence)
        conflict_ids = {eid for c in conflicts for eid in c.evidence_ids}

        scored = []
        for item in evidence:
            rel = self.scorer.score(item, query, evidence)
            penalty = 0.85 if item.evidence_id in conflict_ids else 1.0
            final_score = item.score * rel.reliability * penalty
            scored.append(FusedEvidence(
                evidence_id=item.evidence_id,
                source_type=item.source_type,
                source_id=item.source_id,
                content=item.content,
                retrieval_score=round(item.score, 4),
                reliability=rel.reliability,
                final_score=round(final_score, 4),
                provenance={
                    **item.provenance,
                    "reliability": rel.model_dump(),
                    "conflict_flag": item.evidence_id in conflict_ids,
                },
            ))

        scored.sort(key=lambda x: x.final_score, reverse=True)
        uncertainty = []
        if conflicts:
            uncertainty.append(f"{len(conflicts)} potential evidence conflict(s) detected.")
        if not scored:
            uncertainty.append("No evidence available for fusion.")

        return EvidenceFusionResult(
            evidence=scored[:top_k],
            conflicts=conflicts,
            uncertainty=uncertainty,
        )
