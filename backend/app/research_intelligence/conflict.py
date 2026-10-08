from __future__ import annotations

import re
from .models import EvidenceConflict
from app.reasoning.models import UnifiedEvidence


_NUMBER = re.compile(r"(?<!\w)(\d+(?:\.\d+)?)\s*(g|mg|kg|kcal|%)(?:\b|/)", re.I)
_SERVING = re.compile(r"\b(?:per|/)\s*(\d+(?:\.\d+)?)\s*(g|mg|kg|ml|serving)\b", re.I)


class ConflictDetector:
    """Conservative pairwise conflict detector.

    It flags potential conflicts only when the evidence items are
    plausibly comparable. For food/nutrition evidence, records with
    different food IDs are not treated as conflicting merely because
    they contain different numeric values.
    """

    @staticmethod
    def _comparable(left: UnifiedEvidence, right: UnifiedEvidence) -> bool:
        left_food_id = left.provenance.get("food_id")
        right_food_id = right.provenance.get("food_id")

        if left_food_id and right_food_id:
            return str(left_food_id) == str(right_food_id)

        return True

    def detect(self, evidence: list[UnifiedEvidence]) -> list[EvidenceConflict]:
        conflicts: list[EvidenceConflict] = []

        for i, left in enumerate(evidence):
            for right in evidence[i + 1:]:
                if left.source_type == right.source_type and left.source_id == right.source_id:
                    continue

                if not self._comparable(left, right):
                    continue

                numbers_left = _NUMBER.findall(left.content)
                numbers_right = _NUMBER.findall(right.content)

                if numbers_left and numbers_right:
                    left_values = {(float(v), u.lower()) for v, u in numbers_left}
                    right_values = {(float(v), u.lower()) for v, u in numbers_right}

                    for lv, lu in left_values:
                        for rv, ru in right_values:
                            if lu == ru and abs(lv - rv) > max(0.5, 0.10 * max(lv, rv)):
                                conflicts.append(
                                    EvidenceConflict(
                                        conflict_id=f"conflict:{left.evidence_id}:{right.evidence_id}",
                                        evidence_ids=[left.evidence_id, right.evidence_id],
                                        conflict_type="numeric",
                                        severity=round(
                                            min(1.0, abs(lv - rv) / max(lv, rv)),
                                            4,
                                        ),
                                        explanation=f"Numeric values differ: {lv:g}{lu} vs {rv:g}{ru}.",
                                        resolution="Check serving size, food form, product identity, date, and source authority before selecting a value.",
                                    )
                                )
                                break

                s_left = _SERVING.search(left.content)
                s_right = _SERVING.search(right.content)

                if (
                    s_left
                    and s_right
                    and s_left.group(0).lower() != s_right.group(0).lower()
                ):
                    conflicts.append(
                        EvidenceConflict(
                            conflict_id=f"serving:{left.evidence_id}:{right.evidence_id}",
                            evidence_ids=[left.evidence_id, right.evidence_id],
                            conflict_type="serving_size",
                            severity=0.65,
                            explanation="The evidence uses different serving-size expressions.",
                            resolution="Normalize values to a common serving basis before comparison.",
                        )
                    )

        return conflicts
