
from __future__ import annotations

from .models import EvidenceFusionResult
from .verifier import ClaimVerifier
from .feedback import FeedbackLoopResult, VerificationAttempt
from app.llm.orchestrator import LLMOrchestrator


class VerificationFeedbackLoop:
    """Bounded generate -> verify -> revise loop.

    The loop never exposes hidden reasoning. It only feeds the model concise,
    actionable verification feedback and the evidence itself.
    """

    def __init__(
        self,
        llm: LLMOrchestrator,
        verifier: ClaimVerifier | None = None,
        max_attempts: int = 2,
    ):
        self.llm = llm
        self.verifier = verifier or ClaimVerifier()
        self.max_attempts = max(1, min(max_attempts, 3))

    async def run(
        self,
        query: str,
        initial_answer: str,
        evidence,
        conflicts: list | None = None,
    ) -> FeedbackLoopResult:
        attempts: list[VerificationAttempt] = []
        answer = initial_answer

        for attempt_no in range(1, self.max_attempts + 1):
            verification = self.verifier.verify(
                answer=answer,
                evidence=evidence,
                conflicts=conflicts,
            )

            if verification.answer_allowed:
                attempts.append(VerificationAttempt(
                    attempt=attempt_no,
                    answer=answer,
                    status="accepted",
                    unsupported_claim_count=verification.unsupported_claim_count,
                    uncertainty=verification.uncertainty,
                ))
                return FeedbackLoopResult(
                    final_answer=answer,
                    status="accepted",
                    attempts=attempts,
                    max_attempts_reached=False,
                    final_uncertainty=verification.uncertainty,
                )

            changes = [
                c.claim
                for c in verification.claims
                if c.status in {"unsupported", "uncertain", "contradicted"}
            ]
            attempts.append(VerificationAttempt(
                attempt=attempt_no,
                answer=answer,
                status="needs_revision" if attempt_no < self.max_attempts else "rejected",
                unsupported_claim_count=verification.unsupported_claim_count,
                uncertainty=verification.uncertainty,
                changes_requested=changes[:8],
            ))

            if attempt_no >= self.max_attempts:
                break

            evidence_text = "\n\n".join(
                f"[{item.evidence_id}] {item.content}" for item in evidence
            )
            feedback = "\n".join(
                f"- Remove, qualify, or correct this claim: {claim}"
                for claim in changes[:8]
            ) or "- Use only claims directly supported by the evidence."

            revision_context = (
                "REVISION TASK\n"
                "The previous answer failed evidence verification.\n"
                "Do not invent facts, numbers, sources, or citations.\n"
                "Use only the supplied evidence.\n"
                "If evidence is insufficient, explicitly say that it is insufficient.\n\n"
                f"USER QUESTION:\n{query}\n\n"
                f"EVIDENCE:\n{evidence_text}\n\n"
                f"VERIFICATION FEEDBACK:\n{feedback}\n\n"
                "PREVIOUS ANSWER:\n"
                f"{answer}\n\n"
                "Return a concise corrected answer."
            )

            revised = await self.llm.answer(query, revision_context)
            answer = revised.answer

        return FeedbackLoopResult(
            final_answer=answer,
            status="rejected",
            attempts=attempts,
            max_attempts_reached=True,
            final_uncertainty=[
                "The answer could not be fully verified within the allowed revision attempts."
            ],
        )
