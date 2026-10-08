from pathlib import Path

p = Path(r".\backend\app\research_intelligence\verifier.py")
s = p.read_text()

s = s.replace(
    """        conflicts: list | None = None,
    ) -> VerificationResult:""",
    """        conflicts: list | None = None,
        numerical_calculation=None,
    ) -> VerificationResult:""",
    1,
)

old = """            # Numeric claims remain subject to exact evidence matching.
            if _NUM.search(claim):
                claim_numbers = {
                    m.group(0).lower().replace(" ", "")
                    for m in _NUM.finditer(claim)
                }

                numeric_match = False

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
"""

new = """            # Numeric claims must either match raw evidence exactly or,
            # for deterministic calculations, match the trusted calculated
            # value and its exact evidence record.
            if _NUM.search(claim):
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
"""

if old not in s:
    raise SystemExit("Numeric verification block not found")

s = s.replace(old, new, 1)
p.write_text(s)
print("verifier.py updated")
