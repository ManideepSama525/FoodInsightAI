from __future__ import annotations

import re

from app.orchestration.models import (
    PipelineRequest,
    PipelineResult,
    PipelineStage,
)
from app.reasoning.answer_policy import AnswerPolicy
from app.reasoning.models import ReasoningContext, UnifiedEvidence
from app.reasoning.numerical_service import NumericalReasoningService
from app.research_intelligence.service import ResearchIntelligenceService
from app.llm.orchestrator import LLMOrchestrator


class ProductionPipeline:
    """Application-level integration boundary.

    Coordinates adaptive retrieval, evidence fusion, answer generation,
    claim-level verification, and final response policy.
    """

    def __init__(self):
        self.answer_policy = AnswerPolicy()
        self.research = ResearchIntelligenceService()
        self.llm = LLMOrchestrator()
        self.numerical = NumericalReasoningService()

    @staticmethod
    def _is_evidence_request(query: str) -> bool:
        normalized = query.lower().strip()

        evidence_phrases = (
            "what evidence supports",
            "what evidence support",
            "what is the evidence for",
            "show the evidence",
            "show me the evidence",
            "which evidence supports",
            "what source supports",
            "which source supports",
            "what sources support",
        )

        return any(
            phrase in normalized
            for phrase in evidence_phrases
        )

    @staticmethod
    def _rank_evidence_trace(
        query: str,
        evidence: list[UnifiedEvidence],
    ) -> list[UnifiedEvidence]:
        normalized_query = re.sub(
            r"\s+",
            " ",
            query.lower().strip(),
        )

        def score(item: UnifiedEvidence) -> tuple[float, float]:
            provenance = item.provenance or {}

            food_name = str(
                provenance.get("food_name", "")
            ).lower().strip()

            source = str(
                provenance.get("source", "")
            ).lower().strip()

            content = str(item.content).lower()

            exact_food_match = (
                1.0
                if food_name and food_name in normalized_query
                else 0.0
            )

            food_token_match = 0.0

            if food_name:
                food_tokens = {
                    token
                    for token in re.findall(
                        r"[a-z0-9]+",
                        food_name,
                    )
                    if len(token) >= 3
                }

                query_tokens = {
                    token
                    for token in re.findall(
                        r"[a-z0-9]+",
                        normalized_query,
                    )
                    if len(token) >= 3
                }

                if food_tokens:
                    food_token_match = (
                        len(food_tokens & query_tokens)
                        / len(food_tokens)
                    )

            usda_match = (
                1.0
                if "usda" in source
                else 0.0
            )

            content_match = (
                0.25
                if food_name and food_name in content
                else 0.0
            )

            return (
                exact_food_match * 100.0
                + food_token_match * 20.0
                + usda_match * 5.0
                + content_match,
                float(item.score),
            )

        return sorted(
            evidence,
            key=score,
            reverse=True,
        )

    async def run(
        self,
        request: PipelineRequest,
        vision_result=None,
    ) -> PipelineResult:

        # Preserve the user's original query for the final API result.
        original_query = request.query
        retrieval_query = original_query

        stages = [
            PipelineStage(
                name="understand",
                status="complete",
                details={
                    "mode": request.mode,
                    "has_image": bool(request.image_id),
                },
            )
        ]

        # ------------------------------------------------------------
        # Vision grounding
        # ------------------------------------------------------------
        if vision_result is not None:
            observation = vision_result.observation
            detected_food = observation.food_name

            if detected_food:
                retrieval_query = (
                    f"{original_query}\n"
                    f"Detected food from image: {detected_food}"
                )

                stages.append(
                    PipelineStage(
                        name="vision",
                        status="complete",
                        details={
                            "model": vision_result.model,
                            "food_name": detected_food,
                            "confidence": observation.confidence,
                            "visible_ingredients": (
                                observation.visible_ingredients
                            ),
                            "preparation_characteristics": (
                                observation.preparation_characteristics
                            ),
                            "uncertainty": observation.uncertainty,
                        },
                    )
                )
            else:
                stages.append(
                    PipelineStage(
                        name="vision",
                        status="limited",
                        details={
                            "model": vision_result.model,
                            "food_name": None,
                            "confidence": observation.confidence,
                            "uncertainty": observation.uncertainty,
                            "warnings": observation.warnings,
                        },
                    )
                )

        # ------------------------------------------------------------
        # Existing retrieval pipeline
        # ------------------------------------------------------------
        fused = await self.research.retrieve_and_fuse(
            query=retrieval_query,
            has_image=bool(request.image_id),
            document_ids=None,
            top_k=8,
        )

        retrieval = fused["retrieval"]

        stages.append(
            PipelineStage(
                name="retrieve",
                status=(
                    "complete"
                    if any(
                        retrieval[key] > 0
                        for key in (
                            "vector_count",
                            "lexical_count",
                            "structured_count",
                            "graph_count",
                        )
                    )
                    else "no_evidence"
                ),
                details=retrieval,
            )
        )

        fusion = fused["fusion"]

        evidence = [
            UnifiedEvidence(
                evidence_id=item.evidence_id,
                source_type=item.source_type,
                source_id=item.source_id,
                content=item.content,
                score=item.final_score,
                provenance=item.provenance,
            )
            for item in fusion.evidence
        ]

        context = ReasoningContext(
            query=retrieval_query,
            evidence=evidence,
            graph_relations=[
                e.provenance
                for e in evidence
                if e.source_type == "graph"
            ],
            structured_data=[
                e.provenance
                for e in evidence
                if e.source_type == "structured"
            ],
            observations=[],
            uncertainty=list(fusion.uncertainty),
        )

        numerical_calculation = self.numerical.calculate(
            query=retrieval_query,
            evidence=context.evidence,
        )

        if numerical_calculation is not None:
            stages.append(
                PipelineStage(
                    name="numerical_reasoning",
                    status="complete",
                    details=numerical_calculation.model_dump(),
                )
            )

        if not context.evidence:
            context.uncertainty.append(
                "No retrieval evidence was available."
            )

        policy = self.answer_policy.validate(context)

        stages.append(
            PipelineStage(
                name="reason",
                status="complete",
                details={
                    "grounded": policy["grounded"],
                    "evidence_count": policy["evidence_count"],
                },
            )
        )

        if not context.evidence:
            answer = (
                "I could not retrieve supporting evidence "
                "for this request."
            )

            stages.append(
                PipelineStage(
                    name="validate",
                    status="limited",
                    details=policy,
                )
            )

            stages.append(
                PipelineStage(
                    name="respond",
                    status="complete",
                    details={
                        "model_called": False,
                    },
                )
            )

            return PipelineResult(
                query=original_query,
                answer=answer,
                grounded=False,
                stages=stages,
                uncertainty=context.uncertainty,
                provenance=[
                    evidence.provenance
                    for evidence in context.evidence
                ],
            )

        if self._is_evidence_request(retrieval_query):
            ranked_evidence = self._rank_evidence_trace(
                query=retrieval_query,
                evidence=context.evidence,
            )

            if ranked_evidence:
                top_evidence = ranked_evidence[0]

                top_food_name = str(
                    top_evidence.provenance.get(
                        "food_name",
                        "",
                    )
                ).lower().strip()

                query_lower = retrieval_query.lower()

                if (
                    top_food_name
                    and top_food_name in query_lower
                ):
                    evidence_items = [top_evidence]
                else:
                    evidence_items = ranked_evidence[:5]
            else:
                evidence_items = []

            lines = [
                "The retrieved evidence supporting this request is:"
            ]

            for index, item in enumerate(
                evidence_items,
                start=1,
            ):
                provenance = item.provenance

                source = provenance.get(
                    "source",
                    item.source_type,
                )

                food_name = provenance.get(
                    "food_name",
                    "",
                )

                food_id = provenance.get(
                    "food_id",
                    item.source_id,
                )

                lines.append(
                    f"{index}. {source}"
                    f"{f' — {food_name}' if food_name else ''}"
                    f" (Food ID: {food_id})"
                )

                lines.append(
                    f"   Evidence ID: {item.evidence_id}"
                )

                lines.append(
                    f"   {item.content}"
                )

            answer = "\n".join(lines)

            stages.append(
                PipelineStage(
                    name="evidence_trace",
                    status="complete",
                    details={
                        "evidence_count": len(context.evidence),
                        "returned_count": len(evidence_items),
                        "model_called": False,
                        "ranking_applied": True,
                    },
                )
            )

            stages.append(
                PipelineStage(
                    name="validate",
                    status="complete",
                    details={
                        **policy,
                        "evidence_trace": True,
                    },
                )
            )

            stages.append(
                PipelineStage(
                    name="respond",
                    status="complete",
                    details={
                        "model_called": False,
                        "answer_blocked": False,
                        "evidence_trace": True,
                    },
                )
            )

            return PipelineResult(
                query=original_query,
                answer=answer,
                grounded=True,
                stages=stages,
                uncertainty=context.uncertainty,
                provenance=[
                    evidence.provenance
                    for evidence in context.evidence
                ],
            )

        evidence_text = "\n\n".join(
            f"[Source {index}]\n{evidence.content}"
            for index, evidence in enumerate(
                context.evidence,
                start=1,
            )
        )

        if numerical_calculation is not None:
            evidence_text += (
                "\n\n[Deterministic Numerical Calculation]\n"
                f"Nutrient: {numerical_calculation.nutrient}\n"
                f"Value per 100 g: "
                f"{numerical_calculation.value_per_100g} "
                f"{numerical_calculation.unit}\n"
                f"Requested portion: "
                f"{numerical_calculation.portion_grams} g\n"
                f"Calculated value: "
                f"{numerical_calculation.calculated_value:.3f} "
                f"{numerical_calculation.unit}\n"
                f"Formula: {numerical_calculation.formula}\n"
                f"Food ID: {numerical_calculation.food_id}\n"
                f"Evidence ID: {numerical_calculation.evidence_id}\n"
                f"Source: {numerical_calculation.source}\n"
                "Use this deterministic calculation for the numerical answer."
            )

        response = await self.llm.answer(
            query=original_query,
            context=evidence_text,
        )

        verification = await self.research.verify(
            answer=response.answer,
            evidence=context.evidence,
            numerical_calculation=numerical_calculation,
        )

        validation_details = {
            **policy,
            "claim_verification": {
                "answer_allowed": verification.answer_allowed,
                "unsupported_claim_count": (
                    verification.unsupported_claim_count
                ),
                "claims": [
                    {
                        "claim": claim.claim,
                        "status": claim.status,
                        "support_score": claim.support_score,
                        "evidence_ids": claim.evidence_ids,
                        "explanation": claim.explanation,
                    }
                    for claim in verification.claims
                ],
            },
        }

        stages.append(
            PipelineStage(
                name="validate",
                status=(
                    "complete"
                    if verification.answer_allowed
                    else "blocked"
                ),
                details=validation_details,
            )
        )

        if not verification.answer_allowed:
            contradicted_claims = [
                claim
                for claim in verification.claims
                if claim.status == "contradicted"
            ]

            if contradicted_claims:
                correction = self.research.comparison_correction(
                    claim=contradicted_claims[0].claim,
                    evidence=context.evidence,
                )

                if correction is not None:
                    corrected_answer = correction["answer"]
                    corrected_evidence_ids = correction["evidence_ids"]

                    stages.append(
                        PipelineStage(
                            name="respond",
                            status="complete",
                            details={
                                "model_called": True,
                                "model": self.llm.provider.model_name,
                                "answer_blocked": False,
                                "deterministic_comparison_answer": True,
                                "corrected_from_contradiction": True,
                            },
                        )
                    )

                    return PipelineResult(
                        query=original_query,
                        answer=corrected_answer,
                        grounded=True,
                        stages=stages,
                        uncertainty=[],
                        provenance=[
                            evidence.provenance
                            for evidence in context.evidence
                            if evidence.evidence_id in corrected_evidence_ids
                        ],
                    )

        if not verification.answer_allowed:
            answer = (
                "I could not verify all claims in the generated answer "
                "against the retrieved evidence."
            )

            uncertainty = [
                *context.uncertainty,
                *verification.uncertainty,
            ]

            stages.append(
                PipelineStage(
                    name="respond",
                    status="complete",
                    details={
                        "model_called": True,
                        "model": self.llm.provider.model_name,
                        "answer_blocked": True,
                    },
                )
            )

            return PipelineResult(
                query=original_query,
                answer=answer,
                grounded=False,
                stages=stages,
                uncertainty=list(dict.fromkeys(uncertainty)),
                provenance=[
                    evidence.provenance
                    for evidence in context.evidence
                ],
            )

        supported_ids = []
        uncertain_ids = []

        for claim in verification.claims:
            if claim.status == "supported":
                supported_ids.extend(
                    claim.evidence_ids
                )
            elif claim.status == "uncertain":
                uncertain_ids.extend(
                    claim.evidence_ids
                )

        supported_ids = list(
            dict.fromkeys(supported_ids)
        )

        uncertain_ids = list(
            dict.fromkeys(uncertain_ids)
        )

        if numerical_calculation is not None:
            answer = (
                f"{numerical_calculation.calculated_value:.3f} "
                f"{numerical_calculation.unit}\n\n"
                f"Evidence: {numerical_calculation.evidence_id}"
            )

            citations_added = True

        else:
            answer = response.answer
            citations_added = False

            if supported_ids:
                answer = (
                    f"{answer}\n\n"
                    f"Evidence: {', '.join(supported_ids)}"
                )
                citations_added = True

            if uncertain_ids:
                answer = (
                    f"{answer}\n\n"
                    f"Evidence considered: "
                    f"{', '.join(uncertain_ids)}"
                )
                citations_added = True

        stages.append(
            PipelineStage(
                name="respond",
                status="complete",
                details={
                    "model_called": True,
                    "model": self.llm.provider.model_name,
                    "answer_blocked": False,
                    "deterministic_numerical_answer": (
                        numerical_calculation is not None
                    ),
                    "citations_added": citations_added,
                    "supported_evidence_count": len(
                        supported_ids
                    ),
                    "uncertain_evidence_count": len(
                        uncertain_ids
                    ),
                },
            )
        )

        return PipelineResult(
            query=original_query,
            answer=answer,
            grounded=True,
            stages=stages,
            uncertainty=context.uncertainty,
            provenance=[
                evidence.provenance
                for evidence in context.evidence
            ],
        )
