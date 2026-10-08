from app.safety.models import Evidence, SafetyAssessment, AdulterationSignal

class SafetyService:
    def assess(
        self,
        subject: str,
        hazards: list[str],
        controls: list[str],
        evidence: list[Evidence] | None = None,
    ) -> SafetyAssessment:
        evidence = evidence or []
        uncertainty = []
        if not evidence:
            uncertainty.append("No authoritative evidence was supplied; assessment is informational only.")
        return SafetyAssessment(
            subject=subject,
            status="evidence_review_required" if not evidence else "evidence_supported",
            hazards=hazards,
            controls=controls,
            evidence=evidence,
            uncertainty=uncertainty,
        )

    def evaluate_adulteration(self, signal: AdulterationSignal) -> AdulterationSignal:
        # Signals are retained as observations. The service does not infer fraud
        # or intent from a single indicator.
        if not signal.evidence:
            signal.status = "unverified_signal"
        return signal
