import re
from app.llm.models import LLMResponse
from app.rag.context import CitationRecord

class GroundingValidator:
    def validate(
        self,
        response: LLMResponse,
        citations: list[CitationRecord],
        context: str,
    ) -> tuple[LLMResponse, list[str]]:
        warnings: list[str] = []

        if not context.strip():
            warnings.append("insufficient_evidence")
            response.answer = "I could not find sufficient evidence in the available knowledge base."
            response.source_refs = []
            response.uncertainty = "insufficient_evidence"
            return response, warnings

        valid_indexes = set(range(1, len(citations) + 1))
        invalid = [r.source_index for r in response.source_refs if r.source_index not in valid_indexes]
        if invalid:
            warnings.append("invalid_source_reference")
            response.source_refs = [
                r for r in response.source_refs if r.source_index in valid_indexes
            ]

        if not response.source_refs:
            warnings.append("no_citations_returned")

        # Basic unsupported-claim heuristic: numbers in the answer should normally
        # have a corresponding number in retrieved evidence. This is intentionally
        # conservative and not a substitute for a semantic entailment model.
        answer_numbers = set(re.findall(r"\b\d+(?:\.\d+)?\b", response.answer))
        evidence_numbers = set(re.findall(r"\b\d+(?:\.\d+)?\b", context))
        suspicious = sorted(answer_numbers - evidence_numbers)
        if suspicious:
            warnings.append("numeric_claim_requires_review")
            response.unsupported_claims.extend(
                [f"numeric token {value}" for value in suspicious[:10]]
            )

        return response, warnings
