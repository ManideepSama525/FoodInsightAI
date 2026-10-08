from pathlib import Path

p = Path(r".\diagnose_numerical_pipeline.py")
s = p.read_text()

old = """    verification = await pipeline.research.verify(
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
    )
"""

new = """    verification = await pipeline.research.verify(
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
"""

if old not in s:
    raise SystemExit("Verification block not found")

p.write_text(s.replace(old, new, 1))
print("diagnostic updated")
