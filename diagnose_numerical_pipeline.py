import asyncio

from app.orchestration.pipeline import ProductionPipeline
from app.orchestration.models import PipelineRequest


async def main():
    pipeline = ProductionPipeline()

    fused = await pipeline.research.retrieve_and_fuse(
        query="How much Magnesium is in 246 g of Shrimp creole, no rice?",
        top_k=8,
    )

    evidence = [
        item
        for item in fused["fusion"].evidence
    ]

    context = "\n\n".join(
        f"[Source {i}]\n{item.content}"
        for i, item in enumerate(evidence, start=1)
    )

    calculation = pipeline.numerical.calculate(
        query="How much Magnesium is in 246 g of Shrimp creole, no rice?",
        evidence=[
            __import__("app.reasoning.models", fromlist=["UnifiedEvidence"]).UnifiedEvidence(
                evidence_id=item.evidence_id,
                source_type=item.source_type,
                source_id=item.source_id,
                content=item.content,
                score=item.final_score,
                provenance=item.provenance,
            )
            for item in evidence
        ],
    )

    if calculation:
        context += (
            "\n\n[Deterministic Numerical Calculation]\n"
            f"Nutrient: {calculation.nutrient}\n"
            f"Value per 100 g: {calculation.value_per_100g} {calculation.unit}\n"
            f"Requested portion: {calculation.portion_grams} g\n"
            f"Calculated value: {calculation.calculated_value:.3f} {calculation.unit}\n"
            f"Formula: {calculation.formula}\n"
            f"Food ID: {calculation.food_id}\n"
            f"Evidence ID: {calculation.evidence_id}\n"
            f"Source: {calculation.source}\n"
        )

    response = await pipeline.llm.answer(
        query="How much Magnesium is in 246 g of Shrimp creole, no rice?",
        context=context,
    )

    print("\n=== GENERATED ANSWER ===")
    print(response.answer)

    print("\n=== NUMERICAL CALCULATION ===")
    print(calculation.model_dump() if calculation else None)

    verification = await pipeline.research.verify(
        answer=response.answer,
        evidence=[
            __import__("app.reasoning.models", fromlist=["UnifiedEvidence"]).UnifiedEvidence(
                evidence_id=item.evidence_id,
                source_type=item.source_type,
                source_id=item.source_id,
                content=item.content,
                score=item.final_score,
                provenance=item.provenance,
            )
            for item in evidence
        ],
        numerical_calculation=calculation,
    )

    print("\n=== VERIFICATION ===")
    print("allowed:", verification.answer_allowed)
    print("unsupported:", verification.unsupported_claim_count)

    for claim in verification.claims:
        print("\nCLAIM:", claim.claim)
        print("STATUS:", claim.status)
        print("SCORE:", claim.support_score)
        print("EVIDENCE:", claim.evidence_ids)
        print("EXPLANATION:", claim.explanation)


asyncio.run(main())

