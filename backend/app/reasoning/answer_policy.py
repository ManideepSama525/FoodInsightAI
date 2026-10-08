from app.reasoning.models import ReasoningContext

class AnswerPolicy:
    def validate(self, context: ReasoningContext) -> dict:
        return {
            "grounded": bool(context.evidence),
            "evidence_count": len(context.evidence),
            "uncertainty": context.uncertainty,
            "allowed_claim_types": [
                "evidence_supported_summary",
                "structured_nutrition_value",
                "clearly_labeled_observation",
            ],
            "disallowed_claim_types": [
                "unsupported_regulatory_claim",
                "invented_nutrition_value",
                "unverified_adulteration_conclusion",
            ],
        }
