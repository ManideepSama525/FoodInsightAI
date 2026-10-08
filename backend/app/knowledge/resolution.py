import re
from app.knowledge.models import (
    KnowledgeEntity,
    ResolutionCandidate,
    ResolutionResult,
)

def normalize_name(value: str) -> str:
    value = value.casefold().strip()
    return re.sub(r"[^a-z0-9]+", " ", value).strip()

class EntityResolver:
    def __init__(self, entities: list[KnowledgeEntity] | None = None):
        self.entities = entities or []

    def resolve(self, query: str, entity_type: str | None = None) -> ResolutionResult:
        normalized = normalize_name(query)
        candidates = []

        for entity in self.entities:
            if entity_type and entity.entity_type != entity_type:
                continue

            names = [entity.canonical_name, *entity.aliases]
            normalized_names = [normalize_name(n) for n in names]
            score = 0.0
            matched = []

            if normalized in normalized_names:
                score = 1.0
                matched.append("exact")
            else:
                for name in normalized_names:
                    if normalized and (normalized in name or name in normalized):
                        score = max(score, 0.8)
                        matched.append("substring")

            if score:
                candidates.append(
                    ResolutionCandidate(
                        entity_id=entity.entity_id,
                        canonical_name=entity.canonical_name,
                        entity_type=entity.entity_type,
                        score=score,
                        matched_on=sorted(set(matched)),
                    )
                )

        candidates.sort(key=lambda x: (-x.score, x.canonical_name))
        resolved = None
        status = "unresolved"
        if candidates and candidates[0].score == 1.0:
            exact = [c for c in candidates if c.score == 1.0]
            if len(exact) == 1:
                resolved = exact[0].entity_id
                status = "resolved_exact"
            else:
                status = "ambiguous"
        elif candidates:
            status = "candidate_matches"

        return ResolutionResult(
            query=query,
            candidates=candidates,
            resolved_entity_id=resolved,
            resolution_status=status,
        )
