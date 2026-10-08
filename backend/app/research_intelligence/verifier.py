from __future__ import annotations

import re

from .models import VerificationResult, VerifiedClaim
from app.reasoning.models import UnifiedEvidence
from .semantic_client import SemanticVerifierClient


_SENTENCE = re.compile(r"(?<=[.!?])\s+")
_NUM = re.compile(
    r"(?<!\w)\d+(?:\.\d+)?\s*(?:g|mg|kg|kcal|%)?\b",
    re.I,
)

_COMPARISON = re.compile(
    r"^(?P<left>.+?)\s+has\s+(?P<direction>more|less|higher|lower)"
    r"\s+(?P<nutrient>[a-z][a-z ,()-]+?)\s+than\s+(?P<right>.+?)\.?$",
    re.I,
)

_NON_CLAIM_FRAGMENTS = {
    "yes", "yes.",
    "no", "no.",
    "correct", "correct.",
    "exactly", "exactly.",
    "indeed", "indeed.",
    "right", "right.",
    "okay", "okay.",
    "ok", "ok.",
}


class ClaimVerifier:
    """Evidence-grounded claim verifier.

    V1 lexical verification remains authoritative.
    Semantic similarity is collected as diagnostic evidence for V2
    calibration and does not yet change the blocking policy.

    Structured comparison verification is authoritative when both
    compared foods and the requested nutrient are present in
    structured provenance.
    """

    def __init__(self):
        self.semantic_client = SemanticVerifierClient()

    async def verify(
        self,
        answer: str,
        evidence: list[UnifiedEvidence],
        conflicts: list | None = None,
        numerical_calculation=None,
    ) -> VerificationResult:
        sentences = [
            s.strip()
            for s in _SENTENCE.split(answer.strip())
            if s.strip()
        ]

        claims: list[VerifiedClaim] = []

        for claim in sentences:
            if self._is_non_claim_fragment(claim):
                continue

            comparison_result = self._verify_structured_comparison(
                claim,
                evidence,
            )

            claim_tokens = set(self._tokens(claim))
            scores = []
            supporting_ids = []
            semantic_scores = []

            for item in evidence:
                ev_tokens = set(self._tokens(item.content))

                if not claim_tokens or not ev_tokens:
                    continue

                lexical_overlap = len(
                    claim_tokens & ev_tokens
                ) / max(1, len(claim_tokens))

                if lexical_overlap > 0:
                    scores.append(
                        (lexical_overlap, item.evidence_id)
                    )

                if lexical_overlap >= 0.35:
                    supporting_ids.append(item.evidence_id)

                try:
                    semantic_score = await self.semantic_client.similarity(
                        claim=claim,
                        evidence=item.content,
                    )
                    semantic_scores.append(
                        (semantic_score, item.evidence_id)
                    )
                except Exception as exc:
                    print(f"Semantic verifier error: {exc!r}")

            best = max(scores, default=(0.0, ""))
            best_semantic = max(
                semantic_scores,
                default=(0.0, ""),
            )

            if comparison_result is not None:
                status = comparison_result["status"]
                support_score = comparison_result["support_score"]
                supporting_ids = comparison_result["evidence_ids"]
                comparison_explanation = comparison_result["explanation"]
            elif best[0] >= 0.55:
                status = "supported"
                support_score = best[0]
            elif best[0] >= 0.35:
                status = "uncertain"
                support_score = best[0]
            else:
                status = "unsupported"
                support_score = best[0]

            # Numeric claims must either match raw evidence exactly or,
            # for deterministic calculations, match the trusted calculated
            # value and its exact evidence record.
            if _NUM.search(claim) and comparison_result is None:
                claim_numbers = {
                    m.group(0).lower().replace(" ", "")
                    for m in _NUM.finditer(claim)
                }

                numeric_match = False

                if numerical_calculation is not None:
                    calculated_value = f"{numerical_calculation.calculated_value:.3f}"
                    calculated_unit = str(numerical_calculation.unit).lower()
                    derived_value = f"{calculated_value}{calculated_unit}"
                    exact_evidence_id = str(numerical_calculation.evidence_id)

                    if (
                        derived_value in claim.lower().replace(" ", "")
                        and exact_evidence_id in {
                            item.evidence_id for item in evidence
                        }
                    ):
                        numeric_match = True
                        if best[0] < 0.35:
                            status = "supported"
                            support_score = 1.0
                        supporting_ids = [exact_evidence_id]

                if not numeric_match:
                    for item in evidence:
                        evidence_numbers = {
                            m.group(0).lower().replace(" ", "")
                            for m in _NUM.finditer(item.content)
                        }

                        if (
                            claim_numbers & evidence_numbers
                            and best[0] >= 0.35
                        ):
                            numeric_match = True
                            break

                if not numeric_match:
                    status = "unsupported"

            if comparison_result is not None:
                explanation = comparison_explanation
            else:
                explanation = {
                    "supported": (
                        "Claim has substantial lexical evidence support."
                    ),
                    "uncertain": (
                        "Some evidence overlaps, but support is insufficient "
                        "for a high-confidence decision."
                    ),
                    "unsupported": (
                        "No retrieved evidence sufficiently supports the claim."
                    ),
                }[status]

            if comparison_result is not None:
                explanation = (
                    f"{explanation} "
                    f"Lexical score={best[0]:.4f}; "
                    f"semantic score={best_semantic[0]:.4f}."
                )
            else:
                explanation = (
                    f"{explanation} "
                    f"Lexical score={best[0]:.4f}; "
                    f"semantic score={best_semantic[0]:.4f}."
                )

            claims.append(
                VerifiedClaim(
                    claim=claim,
                    status=status,
                    support_score=round(support_score, 4),
                    evidence_ids=list(
                        dict.fromkeys(supporting_ids)
                    ),
                    explanation=explanation,
                )
            )

        unsupported = sum(
            c.status in {"unsupported", "contradicted"}
            for c in claims
        )

        return VerificationResult(
            claims=claims,
            answer_allowed=bool(claims) and unsupported == 0,
            unsupported_claim_count=unsupported,
            uncertainty=(
                [
                    "One or more claims lack sufficient evidence or "
                    "are contradicted by the retrieved evidence; "
                    "regenerate, qualify, or remove them."
                ]
                if unsupported
                else []
            ),
        )

    @classmethod
    def _verify_structured_comparison(
        cls,
        claim: str,
        evidence: list[UnifiedEvidence],
    ) -> dict | None:
        match = _COMPARISON.match(claim.strip())
        if not match:
            return None

        left_name = cls._normalize_food_name(match.group("left"))
        right_name = cls._normalize_food_name(match.group("right"))
        direction = match.group("direction").lower()
        nutrient_query = cls._normalize_nutrient_name(
            match.group("nutrient")
        )

        if not left_name or not right_name or not nutrient_query:
            return None

        left_item = cls._find_food_evidence(
            left_name,
            nutrient_query,
            evidence,
        )
        right_item = cls._find_food_evidence(
            right_name,
            nutrient_query,
            evidence,
        )

        if left_item is None or right_item is None:
            return None

        left_value = cls._find_nutrient_value(
            left_item,
            nutrient_query,
        )
        right_value = cls._find_nutrient_value(
            right_item,
            nutrient_query,
        )

        if left_value is None or right_value is None:
            return None

        left_amount, left_unit = left_value
        right_amount, right_unit = right_value

        if left_unit != right_unit:
            return None

        if direction in {"more", "higher"}:
            claim_correct = left_amount > right_amount
        else:
            claim_correct = left_amount < right_amount

        evidence_ids = [
            left_item.evidence_id,
            right_item.evidence_id,
        ]

        if claim_correct:
            return {
                "status": "supported",
                "support_score": 1.0,
                "evidence_ids": evidence_ids,
                "explanation": (
                    f"Structured evidence confirms the comparison: "
                    f"{left_item.provenance.get('food_name', left_name)} "
                    f"has {left_amount:g} {left_unit} of {nutrient_query} "
                    f"per 100 g, while "
                    f"{right_item.provenance.get('food_name', right_name)} "
                    f"has {right_amount:g} {right_unit}."
                ),
            }

        return {
            "status": "contradicted",
            "support_score": 1.0,
            "evidence_ids": evidence_ids,
            "explanation": (
                f"Structured evidence contradicts the comparison: "
                f"{left_item.provenance.get('food_name', left_name)} "
                f"has {left_amount:g} {left_unit} of {nutrient_query} "
                f"per 100 g, while "
                f"{right_item.provenance.get('food_name', right_name)} "
                f"has {right_amount:g} {right_unit}."
            ),
        }

    @classmethod
    def comparison_correction(
        cls,
        claim: str,
        evidence: list[UnifiedEvidence],
    ) -> dict | None:
        """Create a deterministic corrected comparison from structured evidence."""
        result = cls._verify_structured_comparison(
            claim,
            evidence,
        )

        if result is None or result["status"] != "contradicted":
            return None

        match = _COMPARISON.match(claim.strip())
        if not match:
            return None

        left_name = cls._normalize_food_name(match.group("left"))
        right_name = cls._normalize_food_name(match.group("right"))
        nutrient = cls._normalize_nutrient_name(
            match.group("nutrient")
        )

        left_item = cls._find_food_evidence(
            left_name,
            nutrient,
            evidence,
        )
        right_item = cls._find_food_evidence(
            right_name,
            nutrient,
            evidence,
        )

        if left_item is None or right_item is None:
            return None

        left_value = cls._find_nutrient_value(
            left_item,
            nutrient,
        )
        right_value = cls._find_nutrient_value(
            right_item,
            nutrient,
        )

        if left_value is None or right_value is None:
            return None

        left_amount, left_unit = left_value
        right_amount, right_unit = right_value

        left_food = str(
            left_item.provenance.get(
                "food_name",
                match.group("left"),
            )
        )
        right_food = str(
            right_item.provenance.get(
                "food_name",
                match.group("right"),
            )
        )

        if left_amount == right_amount:
            answer = (
                f"{left_food} and {right_food} have the same amount "
                f"of {nutrient} ({left_amount:g} {left_unit} per 100 g)."
            )
        elif left_amount > right_amount:
            answer = (
                f"{left_food} has more {nutrient} than {right_food} "
                f"({left_amount:g} {left_unit} vs "
                f"{right_amount:g} {right_unit} per 100 g)."
            )
        else:
            answer = (
                f"{right_food} has more {nutrient} than {left_food} "
                f"({right_amount:g} {right_unit} vs "
                f"{left_amount:g} {left_unit} per 100 g)."
            )

        return {
            "answer": answer,
            "evidence_ids": [
                left_item.evidence_id,
                right_item.evidence_id,
            ],
        }
    @staticmethod
    def _find_food_evidence(
        food_name: str,
        nutrient_query: str,
        evidence: list[UnifiedEvidence],
    ) -> UnifiedEvidence | None:
        candidates = []

        for item in evidence:
            provenance = item.provenance or {}
            item_food = ClaimVerifier._normalize_food_name(
                str(provenance.get("food_name", ""))
            )

            if not item_food:
                continue

            if item_food == food_name:
                if ClaimVerifier._find_nutrient_value(
                    item,
                    nutrient_query,
                ) is not None:
                    candidates.append(item)

        if candidates:
            def reliability_score(item):
                reliability = (item.provenance or {}).get("reliability")

                if isinstance(reliability, dict):
                    value = reliability.get("reliability")
                    if isinstance(value, (int, float)):
                        return float(value)

                if isinstance(reliability, (int, float)):
                    return float(reliability)

                return float(item.score)

            return max(
                candidates,
                key=reliability_score,
            )

        return None

    @staticmethod
    def _find_nutrient_value(
        item: UnifiedEvidence,
        nutrient_query: str,
    ) -> tuple[float, str] | None:
        nutrients = (item.provenance or {}).get("nutrients", {})

        for nutrient_name, nutrient_data in nutrients.items():
            normalized = ClaimVerifier._normalize_nutrient_name(
                str(nutrient_name)
            )

            if normalized == nutrient_query:
                try:
                    return (
                        float(nutrient_data["value_per_100g"]),
                        str(nutrient_data["unit"]).lower(),
                    )
                except (KeyError, TypeError, ValueError):
                    return None

        return None

    @staticmethod
    def _normalize_food_name(text: str) -> str:
        return re.sub(
            r"\s+",
            " ",
            text.lower().strip().rstrip("."),
        )

    @staticmethod
    def _normalize_nutrient_name(text: str) -> str:
        normalized = re.sub(
            r"\s+",
            " ",
            text.lower().strip(),
        )
        normalized = normalized.replace(",", "")
        normalized = normalized.replace("-", " ")
        normalized = re.sub(r"\s+", " ", normalized)

        aliases = {
            "magnesium mg": "magnesium",
            "magnesium": "magnesium",
            "calcium ca": "calcium",
            "calcium": "calcium",
            "sodium na": "sodium",
            "sodium": "sodium",
            "potassium k": "potassium",
            "potassium": "potassium",
            "iron fe": "iron",
            "iron": "iron",
            "zinc zn": "zinc",
            "zinc": "zinc",
            "phosphorus p": "phosphorus",
            "phosphorus": "phosphorus",
            "protein": "protein",
            "fat": "total lipid (fat)",
            "total lipid fat": "total lipid (fat)",
        }

        return aliases.get(normalized, normalized)

    @staticmethod
    def _is_non_claim_fragment(text: str) -> bool:
        return text.strip().lower() in _NON_CLAIM_FRAGMENTS

    @staticmethod
    def _tokens(text: str) -> list[str]:
        return re.findall(r"[a-z0-9]+", text.lower())


